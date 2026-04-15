# Relatório de Progresso — 15 de Abril de 2026

**Projeto:** Sistema de IA para Análise de Solo  
**Autor:** Eduardo Menezes  
**Sessão:** Definição de Arquitetura RAG e Evolução do Sistema

---

## 1. Contexto da Sessão

Esta sessão foi dedicada a seis questões críticas levantadas após o planejamento inicial do dia 14/04:

1. **"O RAG está morto?"** — Avaliação do argumento de que contextos longos (1M tokens) tornam o RAG obsoleto.
2. **Qual arquitetura RAG adotar?** — Análise das 9 arquiteturas mais utilizadas em produção e mapeamento para o contexto do projeto.
3. **Qual modelo de embedding usar?** — Comparativo entre DINOv2, Titan Embeddings G1 (AWS), multilingual-e5-large e alternativas.
4. **Qual banco vetorial usar?** — Comparativo entre pgvector, ChromaDB, Qdrant e alternativas.
5. **Arquitetura do backend Python/FastAPI** — Padrão Clean Architecture, frameworks e estrutura de projeto.
6. **Cinco pontos críticos de arquitetura** — Sessão de brainstorming para definir observabilidade, prompts, chunking, concorrência e fallback.

**Referências analisadas:**

- [RAG Está Morto? Contexto Longo, Grep e o Fim do Vector DB Obrigatório – Akita On Rails](https://akitaonrails.com/2026/04/06/rag-esta-morto-contexto-longo/)
- [9 RAG Architectures Every AI Developer Must Know – Towards AI](https://pub.towardsai.net/rag-architectures-every-ai-developer-must-know-a-complete-guide-f3524ee68b9c)

---

## 2. O RAG Está Morto? — Análise Crítica para o Projeto

### 2.1 O argumento do artigo (Akita On Rails)

O artigo argumenta que **para casos simples e com poucos documentos**, a complexidade de montar um pipeline completo de RAG com VectorDB + embeddings não se justifica. Com modelos de janela de contexto longa (Gemini 1.5 Pro: 1M tokens; Claude: 200k tokens), seria possível simplesmente jogar o documento inteiro na janela e fazer buscas por keyword (grep/BM25) para escolher trechos relevantes.

O autor propõe o conceito de **"Lazy Retrieval"**: busca simples por palavras-chave nos documentos → seleciona os trechos mais relevantes → passa ao LLM. Essencialmente, é **RAG simplificado sem VectorDB**.

### 2.2 Por que o argumento NÃO invalida o RAG para este projeto

| Limitação do contexto longo puro  | Impacto direto no projeto                                                                                                                                                                           |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Limite de tokens insuficiente** | Futuramente haverá: PDFs técnicos + Shapefiles (Agro Lagoa da Prata já existe) + dados climáticos + histórico de safras + especificações de bicos/drones. Volume total excede qualquer janela atual |
| **Custo proibitivo por query**    | Enviar 1M tokens por consulta custa entre $1–$15 por query (Gemini/GPT) — inviável em produção                                                                                                      |
| **Dados não-textuais**            | Shapefiles, CSVs de sensores, dados de drone **não são texto** e não podem ser simplesmente inseridos no contexto                                                                                   |
| **Dados temporais/estruturados**  | Histórico climático e de produtividade por safra exigem SQL e raciocínio temporal, não busca semântica                                                                                              |

### 2.3 O que o artigo oferece de valor — Insight para o MVP

O argumento tem validade **para a Fase 1** (MVP só com PDFs):

> Em vez de montar um pipeline completo com embeddings e ChromaDB imediatamente, o MVP pode começar com **BM25 / TF-IDF + LLM** para validar a hipótese com a engenheira mais rapidamente.

Isso está alinhado com o princípio: _"comece simples, escale a complexidade com evidência"._

#### Decisão adotada:

- **Fase 1 (MVP):** Pode-se optar por retrieval simples (BM25 ou sparse search) + LLM — mais rápido de implementar
- **Fase 2+:** RAG com embeddings densos (**BGE-M3** como modelo primário + ChromaDB) se torna necessário quando o volume de documentos e tipos de dados cresce
- **Fase 3+:** Agentic RAG com múltiplos agentes especializados — **obrigatório** para o escopo completo do sistema

---

## 3. As 9 Arquiteturas RAG — Análise e Mapeamento

Com base no guia de referência, as 9 arquiteturas foram avaliadas em relação ao contexto do projeto:

### 3.1 Resumo das Arquiteturas

| #   | Arquitetura               | Princípio                                                                 | Caso de uso ideal                                      |
| --- | ------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------ |
| 1   | **Standard RAG**          | Busca vetorial simples, top-K chunks → LLM                                | MVP, perguntas simples e diretas                       |
| 2   | **Conversational RAG**    | Memória multi-turno, reescreve a query com histórico                      | Chat contínuo com a engenheira                         |
| 3   | **Corrective RAG (CRAG)** | Avalia qualidade dos chunks antes de passar ao LLM; fallback se inválido  | Alta precisão, domínios onde erro tem custo alto       |
| 4   | **Adaptive RAG**          | Roteador classifica complexidade → escolhe caminho mais barato            | Queries com complexidade variada                       |
| 5   | **Self-RAG**              | Modelo gera tokens de reflexão e se autocorrige em tempo real             | Pesquisa exigente; requer modelo fine-tuned            |
| 6   | **Fusion RAG**            | Gera 3–5 variantes da query, recupera para todas, re-ranqueia             | Perguntas ambíguas ou jargão técnico variado           |
| 7   | **HyDE**                  | Gera uma "resposta hipotética" e usa o vetor dela para buscar docs reais  | Perguntas conceituais ou muito vagas                   |
| 8   | **Agentic RAG**           | Agente planeja, decide quais ferramentas chamar, itera antes de responder | Multi-fonte, multi-tipo de dado, queries complexas     |
| 9   | **GraphRAG**              | Raciocínio sobre entidades e relações em grafo de conhecimento            | Causalidade, multi-hop, domínios com regras explícitas |

### 3.2 Arquiteturas Descartadas para o Projeto

| Arquitetura  | Motivo do descarte (para agora)                                                                                                                             |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Self-RAG** | Exige modelo fine-tuned específico e custo computacional muito alto; não adequado para MVP ou fase inicial                                                  |
| **HyDE**     | Risco de viés: se a "resposta hipotética" sobre solo estiver errada, a busca será guiada na direção errada. Domínio técnico exige precisão, não especulação |
| **GraphRAG** | Alto custo de construção inicial do grafo de conhecimento; reservar para quando os dados de bico, drone e histórico de fazenda estiverem disponíveis        |

---

## 4. Arquitetura RAG Recomendada — Evolução por Fase

### 4.1 Princípio adotado

> _"Comece com Standard RAG. Adicione complexidade apenas com evidência clara de necessidade."_
> — guia de referência analisado

### 4.2 Roadmap de Arquitetura

```
FASE 1 — MVP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Standard RAG (ou Lazy Retrieval / BM25 se VectorDB for prematuro)
+ Conversational RAG (memória multi-turno para o chat com a engenheira)

FASE 2 — Avaliação e Qualidade
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
+ Fusion RAG
  → O usuário vai escrever "pH soja cerrado" — Fusion gera variantes e aumenta recall
+ Corrective RAG (CRAG) ← OBRIGATÓRIO
  → Implementação técnica da Regra de Ouro:
     "Se o score do chunk for baixo, NÃO passa para o LLM.
      Retorna: null + flag sem_cobertura_documental"

FASE 3 — Multi-dado (PDFs + CSV + Shapefile + Clima + Drone)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agentic RAG com Adaptive Router:
  [Agente Documental]   → Standard + Fusion + CRAG sobre PDFs técnicos
  [Agente Espacial]     → GeoPandas sobre Shapefiles da fazenda
  [Agente Temporal]     → SQL sobre histórico de safras e clima
  [Agente Operacional]  → Dados de bicos, máquinas, drones
  [LLM Sintetizador]    → Consolida os resultados → Chat + JSON estruturado

FASE 4 — Raciocínio Relacional
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
+ GraphRAG
  → Para perguntas causais como:
     "Dado esse solo ácido, essa cultura (soja), esse bico (taxa variável),
      esse histórico climático → qual dose de calcário e em que época?"
  → Nó: solo, cultura, bico, clima, dose
  → Aresta: afeta, requer, compensa, limita
```

### 4.3 Decisão de Arquitetura Consolidada

A arquitetura alvo do sistema (Fase 3+) é:

```
                    [Adaptive Router]
                    Classifica a query
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
  [Simples/saudação]  [Factual]      [Complexa/multi-fonte]
  Resposta direta     Standard RAG    Agentic RAG
                           │                │
                      Fusion RAG    ┌────────┴────────────┐
                    (variantes)     │                     │
                          │    Agente PDFs        Agente Dados
                      CRAG Gate    (Standard +    (CSV/Shapefile/
                    (valida score)  Fusion)        Clima/Drone)
                          │                │             │
                          └────────────────┴─────────────┘
                                           ▼
                                  LLM Sintetizador
                                  Chat + JSON output
```

---

## 5. Por que o CRAG é Obrigatório — A Regra de Ouro

O Corrective RAG é o componente central de **confiabilidade** do sistema. Ele implementa diretamente a principal regra de negócio estabelecida na sessão anterior:

> **"Nunca inventar valores numéricos. Se não estiver na fonte, o sistema deve retornar `null` e sinalizar ausência de cobertura."**

#### Como o CRAG implementa essa regra:

```
Query entra
    ↓
Retrieval padrão (busca vetorial Top-K)
    ↓
CRAG Evaluator avalia cada chunk:
    score ≥ 0.7  →  passa para o LLM
    score 0.4–0.7 →  entra no contexto com flag "baixa_confianca"
    score < 0.4  →  descartado
    ↓
Nenhum chunk aprovado?
    → retorna: { resposta: null, flag: "sem_cobertura_documental" }
    → NÃO passa para o LLM
    → NÃO improvisa
```

Este é o mecanismo de prevenção de alucinação mais crítico do sistema.

---

## 6. Decisão sobre Modelo de Embedding

### 6.1 Esclarecimento: DINOv2 não é para texto

O **DINOv2 (Meta)** é um Vision Transformer para embedding de **imagens**, não texto. Não é adequado para RAG sobre PDFs. Só passaria a ser relevante no futuro se o projeto incluir:
- Imagens de solo ou mapas de fertilidade raster
- Análise de imagens de satélite ou drone

### 6.2 Comparativo de Modelos de Embedding para Texto

| Modelo | Dimensões | Suporte PT-BR | Custo | Execução | Observação |
|---|---|---|---|---|---|
| **BGE-M3** (BAAI) | 1024 | Excelente | Grátis | Local | 🏆 Melhor open-source atual — suporta dense + sparse + multi-vector |
| **multilingual-e5-large-instruct** | 1024 | Excelente | Grátis | Local | Upgrade do modelo originalmente planejado |
| **multilingual-e5-large** | 1024 | Excelente | Grátis | Local | Planejado desde sessão 1; sólido e bem documentado |
| **Titan Embeddings G1** (AWS) | 1536 | Bom | Pago (API) | AWS Bedrock | Preso ao ecossistema AWS; inviável para TCC local |
| **text-embedding-3-large** (OpenAI) | 3072 | Excelente | Pago (API) | API | Máxima qualidade, mas custo por token |
| **Cohere embed-multilingual-v3** | 1024 | Excelente | Pago (API) | API | Alternativa comercial sólida |
| **DINOv2** (Meta) | — | — | Grátis | Local | ❌ Modelo de imagem — fora do escopo de texto |

### 6.3 Por que BGE-M3 supera multilingual-e5-large para este projeto

Documentos técnicos da EMBRAPA contêm terminologia muito específica (valores de pH, nomes de nutrientes, siglas agronômicas). O BGE-M3 resolve isso com recuperação em três modos simultâneos:

```
multilingual-e5-large:
  → Dense retrieval apenas
  → Busca por similaridade semântica
  → Pode perder termos exatos como "V% = 60" ou "CTC ph 7"

BGE-M3:
  → Dense retrieval   (semântica — "o que significa?")
  → Sparse retrieval  (BM25-like — "qual palavra exata?")
  → Multi-vector      (ColBERT-style — relevância token a token)
  → Tudo em um único modelo, sem custo extra
```

### 6.4 Decisão de Embedding Adotada

| Contexto | Modelo escolhido | Justificativa |
|---|---|---|
| **MVP e produção local** | `BGE-M3` | Melhor qualidade open-source, roda via `sentence-transformers`, suporte híbrido dense+sparse |
| **Fallback / menor hardware** | `multilingual-e5-large` | Mais leve, já bem testado em PT-BR |
| **Futuro (imagens de solo)** | `DINOv2` | Se o projeto incluir análise de imagens de drones ou mapas raster |
| **Futuro (deploy AWS)** | `Titan Embeddings G1` | Apenas se a infraestrutura migrar para AWS Bedrock |

> **Atualização em relação ao planejamento anterior**: o modelo `multilingual-e5-large` definido na sessão de 14/04 é **substituído pelo BGE-M3** como modelo primário. O `multilingual-e5-large` continua como fallback para ambientes com hardware mais limitado.

---

## 6.5 Perguntas em Aberto para Próximas Sessões

- [ ] Questões adicionais pendentes desta sessão — em andamento

---

## 7. Decisão sobre Banco de Dados Vetorial (VectorDB)

### 7.1 Critério central: compatibilidade com BGE-M3

O BGE-M3 gera simultaneamente três tipos de vetores por documento:

```
BGE-M3 output por chunk:
├── Dense vector   (1024 dims) → busca semântica
├── Sparse vector  (BM25-like) → busca por termos exatos (pH, V%, CTC...)
└── Multi-vector   (ColBERT)   → relevância token a token
```

O VectorDB precisa suportar **sparse vectors** e **named vectors** (múltiplos vetores por documento) para aproveitar totalmente o BGE-M3. Esse critério é determinante na escolha.

### 7.2 Comparativo das Opções

| VectorDB | Sparse Vectors | Named Vectors | Escalabilidade | Execução | Ideal para |
|---|---|---|---|---|---|
| **ChromaDB** | ❌ Não nativo | ❌ Não | ⚠️ Até ~500k docs | Local (SQLite) | Prototipagem rápida / MVP |
| **pgvector** | ⚠️ Limitado | ❌ Não | ⚠️ Até ~1M com HNSW | Local/Servidor Postgres | Infra já usa Postgres; dados estruturados + vetor |
| **Qdrant** | ✅ Nativo completo | ✅ Sim | ✅ Horizontal / bilhões | Docker local ou Qdrant Cloud | Produção com hybrid retrieval |
| **Weaviate** | ✅ Sim (BM25) | ✅ Sim | ✅ Bom | Docker / Cloud | Alternativa ao Qdrant; mais complexo de operar |
| **LanceDB** | ⚠️ Parcial | ✅ Sim | ✅ Serverless | Local / S3 | Integração nativa com Pandas/GeoPandas (Fase 3+) |
| **Milvus / Zilliz** | ✅ Sim | ✅ Sim | ✅✅ Massivo | Docker cluster | Escala de bilhões — overkill para o TCC |
| **FAISS** | ❌ | ❌ | ✅ | Local (biblioteca) | Benchmarks / pesquisa; sem persistência |

### 7.3 Análise das Opções Sugeridas

#### ChromaDB
- **Positivo:** setup zero, Python-nativo, integrado ao LangChain/LlamaIndex
- **Limitação crítica:** não suporta sparse vectors → não aproveita o hybrid retrieval do BGE-M3
- **Uso:** MVP e prototipagem apenas

#### pgvector (PostgreSQL)
- **Positivo:** elimina um serviço da arquitetura se o projeto já usar Postgres para dados estruturados (histórico de safras, receitas agronômicas)
- **Limitação:** sparse vectors imaturos; performance de busca vetorial inferior a soluções dedicadas
- **Uso:** complementar — armazenar dados relacionais + busca vetorial básica na mesma infra

#### Qdrant
- **Positivo:** suporte nativo completo a dense + sparse + named vectors; escrito em Rust (alta performance); payload filters eficientes para metadados agronômicos
- **Sinergiza diretamente com BGE-M3:**

```python
# Qdrant permite armazenar os 3 vetores do BGE-M3 por chunk:
{
    "vectors": {
        "dense":  [0.12, 0.45, ...],          # BGE-M3 dense
        "sparse": {"indices": [...],
                   "values":  [...]}           # BGE-M3 sparse
    },
    "payload": {                               # metadados agronômicos
        "fonte":   "EMBRAPA Cerrado - Boletim 42",
        "pagina":  18,
        "bioma":   "Cerrado",
        "tema":    "calagem",
        "cultura": "soja"
    }
}
```

O CRAG poderá filtrar por `bioma`, `cultura` ou `tema` **antes** da busca vetorial, reduzindo ruído e aumentando a precisão.

### 7.4 Decisão de VectorDB Adotada

| Fase | VectorDB | Justificativa |
|---|---|---|
| **Fase 1 (MVP)** | `ChromaDB` | Zero friction para prototipar; limitação de sparse vectors não impacta nesta fase |
| **Fase 2+ (Produção)** | `Qdrant` | Suporte nativo ao hybrid retrieval do BGE-M3; filtros de metadata agronômica; Docker local |
| **Fase 3+ (Dados estruturados)** | `Qdrant` + `pgvector` | Qdrant para busca vetorial; pgvector dentro do Postgres que armazenará histórico de fazenda e receitas |
| **Fase 3+ (Geoespacial)** | `LanceDB` (avaliação) | Integração nativa com Arrow/GeoPandas pode beneficiar o Agente Espacial |

### 7.5 Stack Tecnológico Consolidado (Fases 1–3)

```
┌─────────────────────────────────────────────────────────┐
│                  STACK DE DADOS DO SISTEMA              │
├─────────────────┬───────────────────────────────────────┤
│   Componente    │   Tecnologia                          │
├─────────────────┼───────────────────────────────────────┤
│ Embedding       │ BGE-M3 (BAAI)                         │
│ VectorDB MVP    │ ChromaDB                              │
│ VectorDB Prod.  │ Qdrant (Docker local → Qdrant Cloud)  │
│ Dados estrut.   │ PostgreSQL + pgvector                 │
│ Dados espaciais │ GeoPandas + LanceDB (avaliação)       │
│ Dados temporais │ PostgreSQL (histórico, clima, safras) │
└─────────────────┴───────────────────────────────────────┘
```

> **Atualização em relação ao planejamento anterior**: o `ChromaDB` definido na sessão de 14/04 como VectorDB único é **substituído pelo Qdrant** na Fase 2+. ChromaDB mantido exclusivamente para o MVP.

---

## 8. Atualização do Roadmap de Fases

Com base nas decisões desta sessão, o roadmap completo é atualizado com embedding e VectorDB:

| Fase | Arquitetura RAG | Embedding | VectorDB | Dados cobertos |
|---|---|---|---|---|
| **Fase 1** | Standard RAG + Conversational | BGE-M3 ou BM25 | ChromaDB | PDFs EMBRAPA |
| **Fase 2** | + Fusion RAG + CRAG | BGE-M3 (dense+sparse) | Qdrant | Mesmos PDFs, mais qualidade |
| **Fase 3** | Agentic RAG multi-agente | BGE-M3 + DINOv2 (imagens) | Qdrant + pgvector | PDFs + CSV + Shapefile + Clima + Drone |
| **Fase 4** | + GraphRAG | BGE-M3 | Qdrant + grafo Neo4j/NetworkX | Raciocínio relacional multi-hop |

---

## 9. Fontes desta Sessão

| Fonte | URL | Relevância |
|---|---|---|
| Akita On Rails — RAG Está Morto? | https://akitaonrails.com/2026/04/06/rag-esta-morto-contexto-longo/ | Debate contexto longo vs RAG; insight sobre MVP simplificado |
| Towards AI — 9 RAG Architectures | https://pub.towardsai.net/rag-architectures-every-ai-developer-must-know-a-complete-guide-f3524ee68b9c | Guia completo com prós/contras de cada arquitetura |
| BGE-M3 — Hugging Face | https://huggingface.co/BAAI/bge-m3 | Modelo de embedding selecionado; paper e documentação técnica |
| BGE-M3 Paper (arXiv) | https://arxiv.org/abs/2402.03216 | M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity |
| Qdrant — Documentação Oficial | https://qdrant.tech/documentation/ | VectorDB selecionado para produção; suporte nativo a sparse+dense |
| pgvector — GitHub | https://github.com/pgvector/pgvector | Extensão PostgreSQL para busca vetorial complementar |

---

_Relatório gerado em 15/04/2026 — Sistema de IA para Análise de Solo — Eduardo Menezes_

---

## 10. Documento de Design Validado

As decisões sobre arquitetura backend e os cinco pontos críticos foram consolidados em documento separado após sessão de brainstorming estruturado:

**Arquivo:** `Docs/design-arquitetura-backend.md`

### Resumo das Cinco Decisões Críticas (Brainstorming 15/04)

| # | Ponto Crítico | Decisão | Justificativa |
|---|---|---|---|
| 1 | **Observabilidade** | Arize Phoenix (local) | Interface visual de traces, zero custo, sem dados saindo da máquina |
| 2 | **Gerenciamento de Prompts** | Templates Jinja2 em `prompts/` | Versionados, editáveis sem mexer no Python, suportam A/B testing |
| 3 | **Chunking** | `RecursiveCharacterTextSplitter` (600t, overlap 80) | Padrão de mercado, respeita fronteiras de parágrafo/frase |
| 4 | **Concorrência** | `run_in_executor` + Celery + Redis | `run_in_executor` para embeddings em query; Celery para ingestão/fine-tuning |
| 5 | **Fallback LLM** | OpenAI com notificação no JSON | Transparente e auditável — `"modelo_usado"` indica a origem de cada resposta |

### Questões Resolvidas (Brainstorming 15/04)

| # | Questão | Decisão | Justificativa |
|---|---|---|---|
| 1 | **Formato dos PDFs** | Pipeline misto com detecção automática | PyMuPDF para PDFs digitais; EasyOCR para escaneados. Garantia para qualquer documento enviado |
| 2 | **Interface da engenheira** | Painel web completo (React/Next.js) | Frontend separado consumindo a FastAPI — histórico, filtros por tema/cultura, métricas de qualidade |
| 3 | **Modelo LLM** | LLaMA 3.1 8B Q4 | Dev: Ollama local (GPU 8-12GB). Prod: llama.cpp CPU no servidor da faculdade (56 cores, ~8-15s/resposta) |
| 4 | **Fine-tuning** | Kaggle Notebooks + Unsloth + QLoRA | Grátis (T4 16GB, 30h/semana), exporta GGUF para o servidor. Custo total: **$0** |

### Infraestrutura Final — Zero Custo

| Componente | Onde | Custo |
|---|---|---|
| API + Serviços | Servidor faculdade (Portainer) | **$0** |
| LLM Inferência | llama.cpp CPU (56 cores) | **$0** |
| VectorDB (Qdrant) | Servidor faculdade | **$0** |
| Fine-tuning | Kaggle Notebooks | **$0** |
| Fallback LLM | OpenAI API (só em falhas) | Mínimo |
| **Total** | | **~$0** |

> Especificações do servidor da faculdade: Intel Xeon E5-2680 v4 (56 cores), 125GB RAM, sem GPU. Gerenciado via Portainer + Docker Compose.
