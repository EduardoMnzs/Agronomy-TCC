# Relatório Técnico — Implantação de LLM Local (llama.cpp)

**Data:** 15 de Abril de 2026  
**Projeto:** TCC — Assistente Inteligente para Análise de Prescrições Agronômicas
**Sessão:** Deployment on-premise do modelo Meta-Llama-3-8B-Instruct  
**Servidor:** `liaa-server-01` (Infraestrutura da Universidade)

---

## 1. Objetivo

Implantar uma API de IA Generativa compatível com o padrão OpenAI, hospedada **100% on-premise** na infraestrutura acadêmica, utilizando o motor `llama.cpp` para inferência CPU-only.

**Justificativa:** Soberania de dados — informações sensíveis de pesquisa, dados da fazenda e documentos técnicos nunca saem dos servidores da instituição. A arquitetura em microsserviços permite integração fluida com demais plataformas hospedadas.

---

## 2. Diagnóstico de Hardware e Decisão Arquitetural

### 2.1 Specs confirmadas do servidor (`liaa-server-01`)

```
CPU:  Intel Xeon E5-2680 v4 — 56 threads lógicas @ 2.40GHz
RAM:  125GB total (~94GB disponível)
GPU:  Não disponível (CPU-only)
Infra: Docker + Portainer (modo Swarm)
```

O mapeamento foi realizado burIando o isolamento do container via mapeamento de `/host`.

### 2.2 Decisão arquitetural: CPU Bound com llama.cpp

Dado a ausência de GPU, adotou-se o `llama.cpp` — motor altamente otimizado para inferência CPU usando instruções **AVX/AVX2**, nativamente suportadas pelos Xeon E5-2680 v4.

### 2.3 Tuning Critical: Resource Starvation Prevention

> **Correção em relação ao planejamento anterior:** o relatório de planejamento sugeria 48 threads. Após análise da arquitetura NUMA do Xeon, o valor correto é **24 threads**.

**Por quê 24 e não 48?**

O Xeon E5-2680 v4 usa arquitetura **NUMA (Non-Uniform Memory Access)** com múltiplos nós. Alocar threads além dos limites de um nó NUMA força acessos à memória remota (latência alta). Além disso, o servidor hospeda outros serviços críticos (MongoDB, proxy reverso) — usar 100% da CPU causaria **Resource Starvation**.

```
56 threads totais disponíveis
├─ 24 threads → llama.cpp (IA) ← configurado
├─ ~20 threads → MongoDB, Caddy, outros serviços
└─ ~12 threads → buffer/overhead do SO
```

**Impacto estimado:** ~10-20 tokens/segundo com LLaMA 8B Q4 — aceitável para análise de prescrições agronômicas.

---

## 3. Modelo Utilizado

| Propriedade | Valor |
|---|---|
| **Modelo** | Meta-Llama-3-8B-Instruct |
| **Formato** | GGUF quantizado (Q4_K_M) |
| **Tamanho** | ~4.7 GB |
| **Compatibilidade** | API OpenAI-compatible (`/v1/chat/completions`) |

---

## 4. Orquestração de Rede e Proxy Reverso (Caddy)

### 4.1 Problema

Expor portas de containers diretamente para a rede da faculdade é uma **falha grave de segurança**.

### 4.2 Solução: Caddy como Proxy Reverso

O container do llama.cpp foi isolado na rede virtual Docker `ingress-network`, compartilhada com os demais serviços. O **Caddy Server** intercepta o tráfego externo (80/443) e encaminha para a porta interna 8080 do container — sem exposição direta.

```yaml
# Trecho do docker-compose.yml com labels Caddy
services:
  llama-cpu:
    image: ghcr.io/ggml-org/llama.cpp:server
    networks:
      - ingress-network
    labels:
      caddy: llama.labs.unimar.br
      caddy.reverse_proxy: "{{upstreams 8080}}"
    command: >
      --model /models/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf
      --host 0.0.0.0
      --port 8080
      --threads 24
      --ctx-size 4096

networks:
  ingress-network:
    external: true

volumes:
  llama_models:
```

**Fluxo de tráfego:**
```
Internet / Rede da faculdade
    ↓  (porta 80/443)
  Caddy Server
    ↓  (roteamento por label: llama.labs.unimar.br)
  Container llama.cpp
    ↓  (porta interna 8080)
  API OpenAI-compatible
```

---

## 5. Persistência de Dados — A Armadilha do Portainer

### 5.1 Falha inicial: Bind Mount relativo

```yaml
# FALHOU no Portainer Swarm
volumes:
  - ./models:/models
```

**Causa:** O Portainer em modo Swarm cria arquivos temporários em diretórios internos próprios. O Docker não encontrava `./models` no host real → `Status: Rejected / invalid mount config`.

### 5.2 Solução: Volume Nomeado

```yaml
# CORRETO para Portainer Swarm
volumes:
  llama_models:/models

volumes:
  llama_models:
```

O daemon do Docker assume a responsabilidade de criar e gerenciar o volume físico em `/var/lib/docker/volumes/llama_models/`, garantindo persistência independente do local de inicialização do container.

> **Lição:** **Nunca usar bind mounts relativos em Portainer Swarm.** Usar sempre volumes nomeados.

---

## 6. Injeção do Modelo — Padrão "Container Sidecar"

### 6.1 O problema

O `llama.cpp` tem comportamento rígido: **crasha imediatamente (Exit 1)** se o arquivo `.gguf` não existir no momento da inicialização. Como injetar um arquivo de 4.7GB em um volume gerenciado pelo Docker sem acesso direto ao filesystem?

### 6.2 Tentativas frustradas

**Tentativa 1:** Override do comando com `sleep infinity` para manter o container vivo enquanto o download era feito via terminal.

- **Resultado:** `invalid argument: sleep` — a imagem possui `ENTRYPOINT` estrito que força a execução do binário do servidor.

**Tentativa 2:** Manteve-se o container em "modo hibernação".

- **Resultado:** `Exit 137 (SIGKILL)` — o `HEALTHCHECK` nativo da imagem assassinou o container ao detectar que a porta 8080 não respondia.

### 6.3 Solução: Padrão Sidecar com Alpine Linux

```yaml
# Container temporário — sem ENTRYPOINT restrito, sem HEALTHCHECK
  model-downloader:
    image: alpine
    volumes:
      - llama_models:/models
    command: >
      sh -c "wget -O llama-8b-solo-q4.gguf "https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf?download=true""
```

**Fluxo:**
```
1. Alpine sobe anexado ao volume llama_models
2. wget baixa o modelo .gguf (4.7GB) para /models/
   → Alpine não tem ENTRYPOINT restrito nem HEALTHCHECK
3. Alpine é destruído após conclusão
4. Container llama.cpp é ativado
   → Encontra o arquivo .gguf → inicializa com sucesso
```

**Por que Alpine funciona:** Imagem micro-Linux minimalista, sem proteções nativas, serve apenas como terminal para executar comandos no volume.

---

## 7. Atualização do Container Registry

### 7.1 Problema

```
Error: image not found: ghcr.io/ggerganov/llama.cpp:server
```

### 7.2 Causa e Correção

O projeto `llama.cpp` cresceu massivamente e migrou o repositório do perfil pessoal (`ggerganov`) para uma organização dedicada (`ggml-org`).

```yaml
# Antigo (não funciona mais)
image: ghcr.io/ggerganov/llama.cpp:server

# Correto (atualizado)
image: ghcr.io/ggml-org/llama.cpp:server
```

> **Impacto no design-arquitetura-backend.md:** atualizado para refletir o novo registry.

---

## 8. Resultado Final

O serviço `llama.cpp` está operacional no servidor da faculdade com:

- API OpenAI-compatible disponível em `llama.labs.unimar.br`
- Inferência CPU-only com LLaMA 3 8B Q4 (~10-20 tokens/s)
- 24 threads configurados (sem starvation dos serviços coabitantes)
- Modelo persistido em volume Docker nomeado (4.7GB)
- Tráfego roteado pelo Caddy (sem portas expostas diretamente)
- Rede isolada em `ingress-network` (segurança)

# Captura de tela do resultado no Portainer Swarm

#### Êxito na instalação do modelo via container sidecar:

![llama model installation](../assets/images/llama-model-installation-2026-04-15%20214428.png)

O modelo foi instalado com sucesso, dentro do volume nomeado `llama_models`. Após a instalação, o container foi destruído.

#### Acesso visual ao modelo

![llama model access](../assets/images/llama-model-access-2026-04-15%20215519.png)

Serviço rodando com sucesso, com API OpenAI-compatible disponível em `llama.labs.unimar.br`.

#### llama CPU Usage:
![llama CPU Usage](../assets/images/llama-cpu-status-2026-04-15%20213711.png)

O modelo está rodando com sucesso, com 24 threads sendo consumidos apenas quando o modelo está sendo utilizado.

#### llama Memory Usage:
![llama Memory Usage](../assets/images/llama-memory-status-2026-04-15%20214136.png)

O modelo está rodando com sucesso, com 4.7GB de RAM alocados.

---

## 9. Lições Aprendidas e Padrões Estabelecidos

| Situação | Problema | Padrão Correto |
|---|---|---|
| **Portainer Swarm + arquivos** | Bind mounts relativos falham | Sempre usar **volumes nomeados** |
| **Injetar dados em volumes** | `ENTRYPOINT` restrito impede acesso | **Padrão Sidecar** com Alpine |
| **Container registry** | Repositório migrou de `ggerganov` → `ggml-org` | Verificar sempre o registry atual |
| **Thread allocation em Xeon** | 100% CPU → starvation | Respeitar limites NUMA: **≤ 24 threads** |
| **Exposição de serviços** | Portas diretas = risco de segurança | Sempre usar **proxy reverso** (Caddy) |

---

## 10. Atualização do Stack Técnico

Com base nesta implantação, os seguintes itens foram confirmados ou corrigidos no design:

| Item | Planejado | Corrigido/Confirmado |
|---|---|---|
| **Container registry** | `ghcr.io/ggerganov/llama.cpp:server` | `ghcr.io/ggml-org/llama.cpp:server` |
| **Threads llama.cpp** | 48 (estimativa) | **24** (respeita NUMA + coabitação) |
| **Volume persistence** | Bind mount `./models` | **Volume Nomeado** `llama_models` |
| **Proxy reverso** | Não definido | **Caddy** com labels Docker |
| **URL da API** | Não definida | `llama.labs.unimar.br` |

---

## 11. Próximos Passos (Infraestrutura)

- [ ] Integrar o endpoint `llama.labs.unimar.br` como LLM client no backend FastAPI
- [ ] Testar o endpoint com queries de análise de prescrições agronômicas (benchmark inicial)
- [ ] Subir demais serviços (Qdrant, PostgreSQL, Redis, FastAPI) via Portainer
- [ ] Configurar o FastAPI para usar `llama.labs.unimar.br` como LLM primário e OpenAI como fallback

---

*Documento gerado em 15/04/2026 — TCC Análise de Prescrições Agronômicas com IA*