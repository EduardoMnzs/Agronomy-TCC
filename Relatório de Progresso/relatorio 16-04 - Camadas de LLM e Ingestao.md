# Relatório Técnico — Implementação das Camadas de LLM, Motor de Ingestão e Celery

**Data:** 16 de Abril de 2026  
**Projeto:** TCC — Assistente Inteligente para Análise de Prescrições Agronômicas
**Sessão:** Backend RAG: Factories de Modelos, Motor BGE-M3 e Filas Assíncronas

---

## 1. Objetivo

Materializar as abstrações projetadas na arquitetura do backend FastAPI, estabelecendo uma ponte sólida e off-line para o RAG. O foco principal engloba a abstração do roteamento de Modelos de Linguagem (LLMs) e a resolução do gargalo de processamento intensivo de documentos agronômicos pesados através de filas assíncronas puras.

**Justificativa:** Garantir o princípio da Inversão de Dependência (SOLID) para que o sistema alterne dinamicamente entre LLMs locais e serviços em nuvem, e solucionar o estrangulamento da API HTTP implementando processamento de fundo (Celery) para PDFs volumosos, assegurando alta disponibilidade e ausência de Timeouts.

---

## 2. Decisões Arquiteturais

### 2.1 Pydantic Settings e Roteamento Dinâmico
A aplicação centraliza o estado através de `config/settings.py`. Como o ecossistema funcionará de forma Híbrida (On-Premise na universidade e Cloud como fallback), injetamos dependências condicionais baseadas na flag `ENVIRONMENT`.

```
Se ENVIRONMENT == "development" → Aciona Ollama (Local/11434)
Se ENVIRONMENT == "production" → Aciona llama.cpp (Servidor Unimar: llama.labs.unimar.br)
Se FALHA → try_catch() aciona FallbackClient (OpenAI, Google, Anthropic ou outro)
```

### 2.2 Desmembramento dos Pacotes LangChain
A arquitetura monolítica antiga do LangChain foi deixada de lado. Instalamos módulos atômicos e dedicados (`langchain-openai`, `langchain-google-genai`, `langchain-anthropic`, `langchain-qdrant`), garantindo um ambiente virtual focado e seguro.

---

## 3. Stack Utilizada (Ingestão)

| Tecnologias Base | Versão/Modulo | Finalidade |
|---|---|---|
| **Embeddings** | `BAAI/bge-m3` | Vetorização Semântica Densa (Multilíngue) via CPU Local |
| **Bando de Dados** | `Qdrant` | VectorDB (Motor C++) via Docker Localhost |
| **Manipulação PDF** | `PyMuPDF` | Extração atômica de textos e detecção de Scans (OCR-ready) |
| **Queues** | `Celery` & `Redis:alpine`| Orquestração de Filas de Trabalho Assíncronas (Broker/Backend) |

---

## 4. Persistência Vetorial

### 4.1 O problema

O design exigia um banco local para o RAG. Inicialmente parametrizado com `ChromaDB`, as instalações pip colapsaram fatalmente no pacote `sqlean-py` base.

**Causa:** O ambiente Python no Windows falhou no cross-compiling das dependências de C++ requeridas pelo módulo SQLite customizado do ChromaDB, travando a subida do servidor.

### 4.2 Solução: Qdrant em Container Docker

A dor de cabeça da biblioteca compilada foi sistematicamente contornada antecipando a migração para a Arquitetura da Fase 2 (Produção). O ChromaDB foi totalmente removido em favor do **Qdrant DB**.

*   Para Dev Isolado sem Docker: `QdrantClient(location=":memory:")`
*   Para Teste Conectado/Produção: Container Docker explícito mantendo o núcleo em Rust veloz.

---

## 5. Falha de Conexão no Banco

### 5.1 O Problema
Ao subir o Docker do Qdrant e testar a ingestão pela classe Python, o terminal estourou a interrupção:
`qdrant_client.http.exceptions.ResponseHandlingException: [SSL: WRONG_VERSION_NUMBER]`

**Causa:** No SDK mais novo da Qdrant (`>=1.7.0`), o construtor usando parâmetros independentes `host="localhost"` e `port=6333` presume agressivamente uso de gRPC e protocolos HTTPS por padrão.

### 5.2 Correção via URI explícita
Modificou-se a abstração no `infrastructure/vectordb/qdrant_adapter.py` condensando as contantes num *Single URI string*:

```python
# Correto (Bypass de SSL automático)
self.client = QdrantClient(
    url=f"http://{self.settings.QDRANT_HOST}:{self.settings.QDRANT_PORT}",
    api_key=self.settings.QDRANT_API_KEY
)
```

---

## 6. Orquestração Assíncrona — Sobrecarga do Event Loop

### 6.1 O problema

O teste com os manuais de Agronomia revelou o teto físico: BGE-M3 rodando em processador sem placa de Vídeo demanda **1 a 1.5s por recorte**. Um PDF de 350 páginas (1.400 rotinas RAG de chunks) amarra a CPU por quase 30 minutos. Manter essa lógica de forma processual causava `Timeout` severo no FastAPI HTTP.

### 6.2 Solução: Message Brokers (Redis + Celery)

Removemos a função vetorial das Views da API para um processo Back-End "cego".

**Fluxo de tráfego Assíncrono:**
```
Frontend Web 
    ↓  (POST /api/v1/ingestion/upload)
  FastAPI Router (Salva em /temp_uploads)
    ↓  (Enfileira com Task ID #XY e Retorna 200 OK para FE)
  Redis Broker (Container local porta 6379)
    ↓  (Fila "agronomy_assistant")
  Celery Ingestion Worker (Processo em janela separada)
    ↓  (BGE-M3 + QdrantDB Insert)
  Retorno do Status no Redis Backend (O FE faz GET no endpoint de API)
```

> **Aviso para Windows Locals:** Por limites da arquitetura SO, para subir o funcionário worker usar explicitamente a flag de enfileiramento linear `--pool=solo`.

---

## 7. Resultado Final

O Pipeline Backend Ingestion RAG encontra-se modularizado, performático e finalizado:
*   Injeção dinâmica de Modelos de Linguagem estabelecida (`dependencies.py`).
*   Vetorização operando através de processamento massivo assíncrono blindando as APIs da porta 8000.
*   BGE-M3 perfeitamente inicializado e armazenando persistência num Docker do Qdrant.
*   Extração inteligente que previne quebras e já alerta documentos em formato de imagens/scans via PyMuPDF.

---

## 8. Lições Aprendidas e Padrões Estabelecidos

| Situação | Problema | Padrão Correto |
|---|---|---|
| **Ambientes C++ Nativos Win** | Compilação trava (ChromaDB API) | Priorizar containers como **Qdrant DB** baseados em Rust |
| **Qdrant Python SDK** | Configuração porta paralela dispara TLS | Uso explícito da cadeia parametral `url="http://..."` |
| **Processamento Local de PDFs** | Limite Teto no FastAPI (> 10s timeout) | **Celery + Redis** para deferral arquitetônico (Event-Driven) |
| **Docker em Foreground** | Terminal perde escopo matando container com SIGINT | Executar via `-d` (Detached mode) persistentemente |

---

## 9. Atualização do Stack Técnico

Com base nesta implantação, os seguintes itens foram confirmados ou re-modelados no design:

| Item | Planejado Originalmente | Corrigido/Confirmado |
|---|---|---|
| **Vector Database Base** | ChromaDB / SQLite | **Qdrant DB** (In Memory/Container) |
| **Assincronicidade de API** | - | **Celery Workers** acoplados ao FastAPI |
| **Mensageria (Broker)** | - | **Redis:alpine** (via Docker localhost:6379) |
| **Monitoramento Interno** | Padrinho Uvicorn CLI | Interface **Flower UI** via porta 5555 |

---

## 10. Próximos Passos (Infraestrutura Lógica)

- [ ] Arquitetar o núcleo conversacional e motor do Agente (Pasta `core/agent`)
- [ ] Construir o fluxograma StateGraph de Decisões do sistema utlizando **LangGraph**
- [ ] Adicionar "Nós" do verificador de qualidade da resposta (Crag Evaluator) e Roteamento Condicional
- [ ] Embutir prompts sistêmicos especializados para o Agronegócio (Fórmulas agronômicas e controle)

---

*Documento gerado em 16/04/2026 — TCC Análise de Prescrições Agronômicas com IA*
