# Design: Arquitetura Backend — Sistema de IA para Prescrições Agronômicas
**Data:** 15/04/2026
**Versão:** 1.0  
**Status:** Planejamento

---

## Sumário

Sistema RAG em Python/FastAPI seguindo Clean Architecture, com BGE-M3 como modelo de embedding, Qdrant como VectorDB de produção e LangGraph para orquestração de agentes. As cinco decisões críticas foram pensadas via sessão de brainstorming e estão documentadas abaixo com seus trade-offs.

---

## Arquitetura

**Padrão:** Clean Architecture (Ports & Adapters)

```
┌─────────────────────────────────────────────────────┐
│           API Layer  (FastAPI routers)              │
├─────────────────────────────────────────────────────┤
│       Application Services  (casos de uso)          │
├─────────────────────────────────────────────────────┤
│          Domain Layer  (RAG, agentes, schemas)      │
├─────────────────────────────────────────────────────┤
│     Infrastructure  (LLM, VectorDB, embeddings)     │
└─────────────────────────────────────────────────────┘
```

**Stack principal:**
- API: `FastAPI` + `Pydantic v2`
- Orquestração RAG (F1–F2): `LangChain`
- Orquestração Agentic (F3+): `LangGraph`
- Embedding: `sentence-transformers` (BGE-M3)
- VectorDB Produção: `Qdrant` (arquivos não estruturados)
- RelationalDB: `PostgreSQL` (Dados API/Zarc e Catálogo de Fontes OBRIGATÓRIO)
- SpatialDB: `PostGIS` (Shapefiles)
- LLM local: `Ollama` (LLaMA 3.1 8B)
- ORM: `SQLAlchemy 2.0 async` + `Alembic`
- Tasks: `Celery` + `Redis`
- Observabilidade: `Arize Phoenix` (local)

---

## Componentes

```
agronomy_assistant/
├── main.py                        # FastAPI lifespan + app init
├── config/
│   ├── settings.py                # Pydantic Settings (.env)
│   └── logging.py                 # Loguru
├── prompts/                       # DECISÃO: Templates Jinja2
│   ├── sistema_solo_v1.jinja2     # Prompt principal
│   └── crag_evaluator_v1.jinja2   # Prompt de avaliação CRAG
├── api/v1/
│   ├── chat.py                    # POST /v1/chat (SSE streaming)
│   ├── ingest.py                  # POST /v1/ingest (async Celery)
│   ├── validate.py                # Painel da engenheira
│   └── dependencies.py            # FastAPI Depends() — DI
├── core/
│   ├── rag/
│   │   ├── pipeline.py            # Orquestrador do fluxo RAG
│   │   ├── retriever.py           # Hybrid retrieval (dense + sparse)
│   │   ├── reranker.py            # CRAG evaluator
│   │   └── generator.py           # LLM + prompt rendering
│   ├── agents/                    # Fase 3: LangGraph
│   │   ├── router.py
│   │   ├── document_agent.py
│   │   ├── spatial_agent.py
│   │   └── temporal_agent.py
│   ├── ingestion/
│   │   ├── pdf_processor.py       # PyMuPDF
│   │   ├── chunker.py             # DECISÃO: RecursiveCharacterTextSplitter
│   │   └── metadata_enricher.py
│   └── schemas/
│       ├── chat.py
│       └── soil_analysis.py       # JSON estruturado de saída
├── infrastructure/
│   ├── vectordb/
│   │   ├── base.py                # Interface abstrata (trocável)
│   │   ├── chroma_adapter.py
│   │   └── qdrant_adapter.py
│   ├── llm/
│   │   ├── base.py
│   │   ├── ollama_client.py
│   │   └── openai_client.py       # DECISÃO: fallback com notificação
│   ├── embeddings/
│   │   └── bge_m3.py              # Singleton via lru_cache
│   └── database/
│       ├── models.py
│       └── repository.py
└── workers/
    ├── ingestion_worker.py        # DECISÃO: Celery para PDFs
    └── finetuning_worker.py       # Celery para fine-tuning (N ≥ 200)
```

---

## Fluxo de Dados

### Query (tempo real)

```
POST /v1/chat
    │
    ├─ 1. Guard Classifier (fora do domínio? → rejeita)
    │
    ├─ 2. Session History (Redis, TTL 30min)
    │       └─ Rewrite query com histórico (Conversational RAG)
    │
    ├─ 3. Fusion RAG → 3 variantes da query
    │
    ├─ 4. Hybrid Retrieval (BGE-M3 dense + sparse → Qdrant)
    │       └─ run_in_executor (não bloqueia event loop)
    │
    ├─ 5. CRAG Evaluator
    │       score ≥ 0.7  → PASS
    │       0.4–0.7      → PASS com flag "baixa_confianca"
    │       < 0.4        → REJECT → retorna null
    │
    ├─ 6. Prompt rendering (Jinja2 template)
    │
    ├─ 7. LLM (Ollama → OpenAI fallback)
    │       → se fallback: "modelo_usado": "gpt-4o-fallback" no JSON
    │
    └─ 8. Output: Chat (SSE stream) + JSON estruturado
```

### Ingestão Multimodal e Híbrida (Background)

A ingestão opera com uma **Taxonomia de Restrição Absoluta**. Todo fluxo exige vínculo intrínseco a uma ID de um `Catálogo de Fontes` que resida no PostgreSQL, prevenindo alucinações.

```text
POST /v1/ingest
    │
    ├─ Valida formato do arquivo
    ├─ Retorna task_id imediatamente (não bloqueia)
    │
    └─ Celery Worker (Parsers Especializados):
        ├─ Trilha Vetorial (PDFs/OCR):
        │    ├─ RecursiveCharacterTextSplitter (600t, overlap 80)
        │    ├─ Atribui metadados OBRIGATÓRIOS (id_fonte, página)
        │    └─ Upsert no Qdrant
        │
        ├─ Trilha Relacional (CSV/APIs - ex: Zarc):
        │    ├─ Validação de Schema Pydantic
        │    └─ INSERT no PostgreSQL (isolado do Vectordb)
        │
        └─ Trilha Espacial (SHP):
             ├─ GeoPandas extrai polígonos
             └─ Salva no PostGIS atrelado à chave estrangeira da cultura

GET /v1/ingest/{task_id} → status do processamento
```

---

## Tratamento de Erros

### Decisões Validadas

| Cenário | Comportamento |
|---|---|
| **CRAG: nenhum chunk aprovado** | `{ "resposta": null, "flag": "sem_cobertura_documental" }` — nunca inventa |
| **Ollama offline** | Fallback silencioso para OpenAI + `"modelo_usado": "gpt-4o-fallback"` no JSON |
| **OpenAI também offline** | `503 LLM_UNAVAILABLE` com mensagem clara |
| **Qdrant offline** | Fallback para ChromaDB + `"vectordb_fallback": true` no JSON |
| **Query fora do domínio** | Guard Classifier rejeita antes de qualquer LLM call |
| **PDF corrompido** | Worker Celery registra erro + status `FAILED` no `task_id` |
| **BGE-M3 OOM** | Retry com batch menor; fallback para `multilingual-e5-large` |

### Princípio central

> **Nunca inventar valores numéricos.** Se não estiver na fonte com score ≥ 0.7, o sistema retorna `null` e sinaliza `sem_cobertura_documental`. Esta regra não tem exceções.

---

## Cinco Decisões Críticas (Brainstorming 15/04)

| # | Decisão | Escolha | Justificativa |
|---|---|---|---|
| 1 | **Observabilidade** | Arize Phoenix (local) | Interface visual de traces, zero custo, sem dados saírem da máquina |
| 2 | **Gerenciamento de Prompts** | Templates Jinja2 em `prompts/` | Versionados, editáveis sem mexer no Python, permite A/B testing |
| 3 | **Chunking** | `RecursiveCharacterTextSplitter` (600t, overlap 80) | Padrão do mercado, respeita fronteiras de parágrafo/frase, comparável em benchmark |
| 4 | **Concorrência** | `run_in_executor` + Celery + Redis | `run_in_executor` para embeddings em query; Celery para ingestão de PDFs e fine-tuning |
| 5 | **Fallback LLM** | OpenAI com notificação no JSON | Transparente e auditável — `"modelo_usado"` indica a origem de cada resposta |

---

## Observabilidade

**Ferramenta:** Arize Phoenix (local, open-source)

O que é rastreado por query:
```python
{
  "query_id": "uuid",
  "query_original": "...",
  "query_rewritten": "...",      # após Conversational RAG
  "chunks_retrieved": [
    {"id": "chunk_042", "score": 0.87, "fonte": "...", "pagina": 18},
  ],
  "crag_decisions": {"chunk_042": "PASS", "chunk_015": "REJECT"},
  "llm_used": "llama-8b-solo-q4.gguf",     # ou "gpt-4o-fallback"
  "latencia_retrieval_ms": 124,
  "latencia_llm_ms": 1840,
  "flag_requer_validacao": false
}
```

---

## Estratégia de Testes

| Camada | Ferramenta | O que testar |
|---|---|---|
| **Unitários** | `pytest` | Chunker, Parser Zarc, CRAG evaluator, schemas Pydantic |
| **Integração** | `pytest-asyncio` | Pipeline RAG completo com VectorDB e Banco Relacional reais |
| **LLM/VectorDB mock** | `pytest-mock` | Testar fallback sem Ollama ou Qdrant |
| **Avaliação IR** | Dataset `Ground Truth` | Ingestão testada medindo NDCG/MRR (a fonte EXATA precisa estar no TOP-3 do retorno do ORCA/Roteador) |
| **Avaliação RAG** | `ragas` | Faithfulness, Answer Relevancy, Context Recall |
| **Benchmark** | Validadores (Kpis) | Validação cega do modelo junto da engenheira agrônoma |

---

## Infraestrutura de Execução

### Ambientes

| Ambiente | Onde roda | Propósito |
|---|---|---|
| **Desenvolvimento** | Máquina local (GPU 8-12GB) | Ollama + LLaMA 8B Q4 para iteração rápida |
| **Produção** | Servidor faculdade (Portainer) | Todos os serviços + llama.cpp CPU |
| **Fine-tuning** | Kaggle Notebooks (grátis) | GPU T4/P100 16GB, 30h/semana |

### Servidor da Faculdade — Specs

```
CPU:  Intel Xeon E5-2680 v4 — 56 cores @ 2.40GHz
RAM:  125GB total (~94GB disponível)
GPU:  Não disponível (CPU-only)
Infra: Docker + Portainer
```

### Docker Compose (serviços no servidor)

```yaml
services:
  api:        # FastAPI              ~200MB RAM
  worker:     # Celery worker        ~300MB RAM
  redis:      # Broker + sessões     ~100MB RAM
  qdrant:     # VectorDB produção    ~500MB RAM
  postgres:   # Dataset Store        ~200MB RAM
  phoenix:    # Arize Phoenix        ~500MB RAM
  llama-cpu:  # llama.cpp servidor   ~5GB  RAM
              # ─────────────────────────────────
              # Total estimado:      ~7GB  RAM

  # llama-cpu config (valores confirmados em produção 15/04):
  # image: ghcr.io/ggml-org/llama.cpp:server
  # --model /models/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf
  # --threads 24
  # --ctx-size 4096
  # Latência estimada: ~10-20 tokens/s (~8-15s por resposta)
  # URL da API: llama.labs.unimar.br (via Caddy proxy reverso)
  # Volume: llama_models (nomeado — nunca bind mount relativo no Swarm)
```

> **Padrões estabelecidos em produção (15/04):**
> - Sempre usar **volumes nomeados** no Portainer Swarm (bind mounts relativos falham)
> - **Padrão Entregador (Alpine)** para injetar arquivos grandes em volumes Docker
> - Registry correto: `ghcr.io/ggml-org/llama.cpp:server` (projeto migrou de `ggerganov`)
> - **24 threads** máximo para respeitar limites NUMA e não causar starvation
> - NUMA: Non-Uniform Memory Access, uma arquitetura de memória distribuída que permite que diferentes processadores acessem diferentes partes da memória em velocidades diferentes. No servidor da faculdade, temos 48 cores disponíveis, mas apenas 24 podem ser usados para o llama.cpp.
> - Starvation: é uma situação em que um processo não consegue obter os recursos de que precisa para ser executado, como tempo de CPU, memória ou acesso a dispositivos de E/S.

### Pipeline de Fine-Tuning (zero custo)

```
Kaggle Notebook (GPU T4/P100 16GB — grátis 30h/semana):
  1. Carrega Dataset Store (pares Q&A validados pela engenheira)
  2. Fine-tuna LLaMA 3.1 8B com Unsloth + QLoRA 4-bit (~2-3h)
  3. Exporta LoRA adapter (.safetensors, ~200MB)
  4. Merge adapter → modelo base
  5. Converte para GGUF (formato llama.cpp)
  6. Upload para o servidor da faculdade

Servidor (pós fine-tuning):
  7. llama-cpu serve o modelo especializado em prescrições agronômicas
```

---

## Questões Resolvidas (Brainstorming 15/04)

| # | Questão | Decisão |
|---|---|---|
| 1 | **Formato dos PDFs** | Misto — pipeline detecta automaticamente: digital via PyMuPDF, escaneado via EasyOCR |
| 2 | **Interface da engenheira** | Painel web completo (React/Next.js) consumindo a FastAPI — histórico, filtros, métricas |
| 3 | **Modelo LLM** | LLaMA 3.1 8B Q4 — local (Ollama, GPU 8-12GB dev) + llama.cpp CPU (56 cores, servidor) |
| 4 | **Fine-tuning** | Kaggle Notebooks (grátis, T4 16GB, 30h/sem) + Unsloth + QLoRA → exporta GGUF para servidor |

## Custos do Sistema

| Componente | Custo |
|---|---|
| Servidor da faculdade | **$0** — on-premise via Portainer |
| LLM Inferência (llama.cpp CPU) | **$0** |
| Fine-tuning (Kaggle) | **$0** |
| VectorDB (Qdrant self-hosted) | **$0** |
| Fallback LLM (OpenAI) | Mínimo — só em falhas |
| **Total operacional** | **~$0** |

---

*Design pensado em 15/04/2026 via sessão de brainstorming — Sistema de IA para Análise de Prescrições Agronômicas*
