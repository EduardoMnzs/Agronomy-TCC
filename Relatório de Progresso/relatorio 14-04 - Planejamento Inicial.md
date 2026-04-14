# Relatório de Planejamento Inicial — Sistema de IA para Análise de Solo
**Data:** 14 de Abril de 2026  
**Projeto:** TCC — Assistente Inteligente para Análise de Solo
**Versão:** 1.0  
**Status:** Planejamento

---

## 1. Objetivo do Projeto

Desenvolver um sistema de Inteligência Artificial capaz de:

1. **Ingerir e compreender** documentos técnicos da EMBRAPA (exemplo) (PDFs, boletins, manuais de solo)
2. **Responder perguntas** em linguagem natural sobre análise de solo, recomendações agronômicas, calagem, adubação, culturas e biomas
3. **Analisar arquivos de dados** enviados pelo usuário (planilhas, CSVs, shapefiles) e gerar diagnósticos estruturados
4. **Evoluir continuamente** com base na validação de uma engenheira agrônoma especialista
5. **Exportar respostas** em dois formatos: chat conversacional e JSON estruturado (para integração com sistemas externos, ou evolução do projeto)

---

## 2. Contexto e Motivação

A EMBRAPA (Empresa Brasileira de Pesquisa Agropecuária) possui um vasto acervo de publicações técnicas sobre solo, culturas e recomendações agronômicas. Assim como outras empresas com publicações e documentações profundas sobre temas relacionados. No entanto, esse conhecimento está distribuído em centenas de documentos, dificultando consultas rápidas e precisas por parte de técnicos e produtores.

O sistema proposto atua como um **assistente especialista de solo**, tornando esse conhecimento acessível de forma conversacional, rastreável e auditável — com a engenheira agrônoma como validadora do processo.

---

## 3. Abordagem Técnica Escolhida: RAG + Fine-tuning (Híbrida)

### Por que híbrida?

| Abordagem | Velocidade de implantação | Custo | Especificidade no domínio |
|---|---|---|---|
| RAG puro | Alta | Baixo | Média |
| Fine-tuning puro | Baixa | Alto | Alta |
| **RAG + Fine-tuning** | **Alta no MVP** | **Crescente** | **Muito Alta** |

A abordagem híbrida permite:
- **Fase MVP**: início imediato com RAG, sem necessidade de datasets anotados
- **Fase 2**: melhoria contínua via fine-tuning com os pares validados pela engenheira
- **Escalabilidade**: novos documentos são adicionados ao VectorDB sem retreinamento completo

---

## 4. Arquitetura do Sistema

### 4.1 Diagrama Geral

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE INGESTÃO                       │
│                                                             │
│  PDFs → Extração → Chunking → Embeddings → VectorDB         │
│  (futuro: Shapefiles, CSVs, PostgreSQL)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    CAMADA DE INFERÊNCIA                     │
│                                                             │
│  Pergunta → Guard Classifier → Embedding da Query           │
│           → Busca Vetorial (Top-K) → Montagem de Prompt     │
│           → LLM Core → Auto-avaliação → Output Formatter    │
│                                                             │
│  Saída: Chat  |  JSON Estruturado                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  CAMADA DE VALIDAÇÃO                        │
│                                                             │
│  Engenheira valida (correto/incorreto) → Dataset Store (.jsonl)          │
│  Quando N ≥ 200 pares → Fine-tuning Pipeline                │
│  Novo modelo → A/B test vs. versão anterior                 │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Descrição dos Componentes

| Componente | Responsabilidade | Tecnologia Recomendada |
|---|---|---|
| **Ingestor de PDFs** | Extrai texto, limpa e divide em chunks semânticos | `PyMuPDF`, `pdfplumber`, `LangChain document loaders` |
| **Chunker Semântico** | Divide texto em blocos de ~500 tokens com overlap de 50 | `LangChain RecursiveCharacterTextSplitter` |
| **Embedding Engine** | Vetoriza chunks e queries | `multilingual-e5-large` (local) ou `text-embedding-3-small` (OpenAI) |
| **Vector Database** | Armazena vetores e metadados, realiza busca por similaridade | `ChromaDB` (local/MVP) ou `Weaviate` (cloud) |
| **Guard Classifier** | Filtra perguntas fora do domínio agrícola/solo | `BERT` fine-tuned (v2) ou heurística de keywords (MVP) |
| **LLM Core** | Raciocínio, geração de resposta com base no contexto | `LLaMA 3.1 8B` (local) ou `GPT-4o`/`Gemini 1.5 Pro` (API) |
| **Auto-avaliador** | LLM avalia sua própria resposta antes de retornar | Segundo prompt ao mesmo LLM |
| **Output Formatter** | Gera resposta em Chat e/ou JSON validado por schema | `Pydantic v2` |
| **Interface de Chat** | Frontend conversacional para usuário/engenheira | `Streamlit` (MVP) ou `FastAPI + React` (v2) |
| **Módulo de Validação** | Painel para a engenheira aprovar/rejeitar respostas | Tela simples com (correto/incorreto) + campo de anotação |
| **Dataset Store** | Persiste pares Q&A validados para fine-tuning | SQLite + exportação `.jsonl` |
| **Fine-tuning Pipeline** | Retreina o LLM base com dados validados | `Hugging Face PEFT + LoRA`, `Unsloth` |
| **Conector Futuro** | Suporte a Shapefiles, CSVs, banco de dados | `GeoPandas`, `Pandas`, `SQLAlchemy` |

---

## 5. Fluxo de Dados Detalhado

### Fluxo A — Ingestão (executado pela engenheira, offline)

```
   PDF
    │
    ▼
[1] Extração de Texto         ← PyMuPDF / pdfplumber
    │  Remove cabeçalhos/rodapés, normaliza encoding
    ▼
[2] Chunking Semântico        ← LangChain RecursiveCharacterTextSplitter
    │  Blocos ~500 tokens, overlap ~50 tokens
    │  Metadados por chunk: {fonte, página, seção, data_publicacao, tema}
    ▼
[3] Geração de Embeddings     ← multilingual-e5-large
    │  Vetor de 1024 dimensões por chunk
    ▼
[4] Armazenamento no VectorDB ← ChromaDB
    │  Indexado com metadados para filtro por bioma, cultura, etc.
    ▼
   Base de Conhecimento Pronta para consulta
```

### Fluxo B — Query em Tempo Real

```
Usuário envia pergunta
    │
    ▼
[1] Guard Classifier          ← detecta se é sobre solo/agronomia
    │  Se não → recusa educada imediata
    ▼
[2] Extração de Entidades     ← NER ou prompt estruturado
    │  Identifica: pH, cultura, nutrientes, região, coordenadas
    ▼
[3] Embedding da Query        ← mesmo modelo do Fluxo A
    ▼
[4] Busca Vetorial Top-K      ← ChromaDB similarity search (K=5)
    │  Retorna chunks mais relevantes + scores de similaridade
    ▼
[5] Score < threshold?
    │  Sim → flag "sem_cobertura_documental" → resposta de fallback
    ▼
[6] Montagem do Prompt        ← [instrução de sistema] + [chunks] + [pergunta]
    ▼
[7] LLM gera resposta         ← LLaMA 3 / GPT-4o / Gemini
    ▼
[8] Auto-avaliação do LLM    ← segundo prompt: "Você usou apenas as fontes?"
    │  Incerto → flag "requer_validacao: true"
    ▼
[9] Output Formatter          ← Pydantic schema
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
   Chat               JSON           Ambos (padrão)
    │
    ▼
[10] Módulo de Validação      ← Engenheira avalia (Correto / Incorreto / Parcialmente Correto)
    │
    ├── (Correto) → salva no Dataset Store
    └── (Incorreto / Parcialmente Correto) → descarta ou anota tipo de erro
                │
                ▼ (quando N ≥ 200 pares)
[11] Fine-tuning Pipeline     ← PEFT + LoRA sobre LLaMA base
                │
                ▼
       Novo modelo avaliado vs. anterior no benchmark set
```

---

## 6. Esquema JSON de Saída

```json
{
  // --- RESPOSTA PRINCIPAL ---
  "resposta": "Solo ácido com pH 5.2, recomenda-se calagem.",

  // --- RASTREABILIDADE ---
  "query_id": "3f7a9b12-4c8d-4e2f-a1b0-9d6e5c3f2a11",
  "timestamp": "2026-04-14T17:50:00-03:00",
  "modelo_versao": "rag-v1.2 | llama3-finetune-v0.3",
  "modo_saida": "json",
  "tokens_usados": 412,

  // --- FONTES UTILIZADAS ---
  "fontes": [
    {
      "titulo": "Embrapa Cerrado - Boletim Técnico 42",
      "pagina": 18,
      "trecho": "Para pH abaixo de 5.5, recomenda-se a aplicação de calcário..."
    }
  ],

  // --- PARÂMETROS EXTRAÍDOS DO SOLO ---
  "parametros_solo": {
    "pH": 5.2,
    "materia_organica_pct": null,
    "fosforo_ppm": null,
    "potassio_cmolc": null,
    "calcio_cmolc": null,
    "magnesio_cmolc": null,
    "aluminio_cmolc": null,
    "saturacao_bases_pct": null,
    "CTC": null
  },

  // --- CONTEXTO AGRONÔMICO ---
  "cultura_alvo": "soja",
  "regiao": "Cerrado",
  "bioma": "Cerrado",
  "coordenadas": { "lat": null, "lon": null },

  // --- REGIÃO GEOGRÁFICA ---
  "regiao": "Sudeste",
  "estado": "São Paulo",
  "municipio": "Piracicaba",
  "coordenadas": { "lat": -22.7273, "lon": -47.6428 },

  // --- RECOMENDAÇÕES ESTRUTURADAS ---
  "recomendacoes": [
    {
      "tipo": "calagem",
      "descricao": "Aplicar calcário para elevar pH a 6.0-6.5",
      "prioridade": "alta",
      "quantidade_estimada": "2.5 t/ha",
      "produto_sugerido": "Calcário dolomítico PRNT >= 90%",
      "epoca_aplicacao": "90 dias antes do plantio"
    }
  ],

  // --- ALERTAS E SEVERIDADE ---
  "nivel_alerta": "moderado",
  "flags": ["solo_acido", "risco_toxidez_aluminio"],

  // --- QUALIDADE E CONTROLE ---
  "qualidade": {
    "confianca": 0.87,
    "requer_validacao": false,
    "validado_por_especialista": false,
    "cobertura_documental": "parcial",
    "alertas_sistema": []
  },

  // --- METADADOS PARA DOWNSTREAM ---
  "input_original": "Qual a recomendação para solo com pH 5.2 para soja?"
}
```

> **Nota:** Campos `null` indicam ausência de informação — nunca são preenchidos com estimativas sem base documental.

---

## 7. Tratamento de Erros

### Estratégia em Camadas (MVP → v2)

#### Camada 1 — MVP: Threshold + Auto-Avaliação
```
Pergunta → Score de similaridade < 0.6? → fallback com aviso
         → LLM gera → auto-avalia → incerto? → flag "requer_validacao"
```

#### Camada 2 — v2: Guard Classifier
Modelo BERT treinado para detectar:
- Pergunta fora do domínio de solo → rejeição imediata
- Cobertura insuficiente no VectorDB → aviso proativo

### Tabela de Cenários de Erro

| Cenário | Detecção | Comportamento |
|---|---|---|
| Confiança baixa (< 0.6) | Score retrieval | Avisa usuário, sinaliza para validação |
| Pergunta fora do domínio | Guard Classifier / keywords | Recusa educada |
| Nenhum chunk relevante | Similaridade abaixo do threshold | `"resposta": null`, flag `sem_cobertura` |
| Possível alucinação | LLM auto-avaliação negativa | `"requer_validacao": true` |
| PDF corrompido | Erro na extração | Skip + log + alerta para engenheira |
| Campo numérico ausente | Entidade não extraída | `null` explícito — nunca interpola valores |
| Falha na API do LLM | Exception + timeout | Retry 2x → resposta mínima com fonte direta |

### Regras

> **NUNCA inventar valores numéricos de solo** (pH, ppm, t/ha) sem base documental explícita.
> **Score de confiança ≠ correção factual** — o loop de validação da engenheira é insubstituível.
> **Toda resposta deve citar a fonte** — sem fonte, a resposta vai como `"cobertura_documental": "ausente"`.

---

## 8. Ferramentas e Tecnologias — Fontes e Links

### 8.1 Extração e Processamento de Documentos

| Ferramenta | Uso | Link |
|---|---|---|
| **PyMuPDF (fitz)** | Extração de texto de PDFs com alta fidelidade | https://pymupdf.readthedocs.io |
| **pdfplumber** | Extração de tabelas e texto de PDFs | https://github.com/jsvine/pdfplumber |
| **Unstructured.io** | Parsing avançado de PDFs, imagens, HTML | https://docs.unstructured.io |
| **LangChain Document Loaders** | Pipeline de ingestão multi-formato | https://python.langchain.com/docs/modules/data_connection/document_loaders |
| **LlamaIndex** | Framework RAG completo e extensível | https://docs.llamaindex.ai |

### 8.2 Embeddings

| Ferramenta | Modelo | Link |
|---|---|---|
| **sentence-transformers** | `multilingual-e5-large` (suporta PT-BR) | https://www.sbert.net |
| **OpenAI Embeddings** | `text-embedding-3-small` (API) | https://platform.openai.com/docs/guides/embeddings |
| **Hugging Face** | Modelos open-source de embedding | https://huggingface.co/models?pipeline_tag=feature-extraction |
| **BGE-M3** | Embedding multilingual de alta qualidade (local) | https://huggingface.co/BAAI/bge-m3 |

### 8.3 Bancos Vetoriais

| Ferramenta | Perfil | Link |
|---|---|---|
| **ChromaDB** | Local, fácil setup, ideal para MVP | https://docs.trychroma.com |
| **FAISS** | Altamente performático, desenvolvido pelo Meta | https://faiss.ai |
| **Weaviate** | Cloud e local, suporte a filtros avançados | https://weaviate.io/developers/weaviate |
| **Qdrant** | Moderna, rápida, suporte a payloads ricos | https://qdrant.tech/documentation |
| **Pinecone** | Cloud gerenciado, escalável | https://docs.pinecone.io |

### 8.4 LLMs — Modelos Base

| Modelo | Tipo | Melhor para | Link |
|---|---|---|---|
| **LLaMA 3.1 8B / 70B** | Open-source, local | Fine-tuning, privacidade | https://huggingface.co/meta-llama |
| **Mistral 7B / Mixtral** | Open-source, local | Eficiência, custo | https://huggingface.co/mistralai |
| **GPT-4o** | API (OpenAI) | Qualidade máxima | https://platform.openai.com |
| **Gemini 1.5 Pro** | API (Google) | Contexto longo (1M tokens) | https://ai.google.dev |
| **Qwen2.5** | Open-source, local | Multilingual, suporte PT | https://huggingface.co/Qwen |

### 8.5 Fine-tuning

| Ferramenta | Uso | Link |
|---|---|---|
| **Hugging Face PEFT** | Fine-tuning com LoRA e QLoRA | https://huggingface.co/docs/peft |
| **Unsloth** | Fine-tuning 2x mais rápido, menos VRAM | https://github.com/unslothai/unsloth |
| **Axolotl** | Framework completo de fine-tuning | https://github.com/OpenAccess-AI-Collective/axolotl |
| **LLaMA Factory** | Interface amigável para fine-tuning | https://github.com/hiyouga/LLaMA-Factory |
| **TRL (Hugging Face)** | Treinamento com RLHF e DPO | https://huggingface.co/docs/trl |

### 8.6 Frameworks RAG

| Ferramenta | Uso | Link |
|---|---|---|
| **LangChain** | Pipeline RAG modular, amplo ecossistema | https://python.langchain.com |
| **LlamaIndex** | RAG especializado em dados estruturados e docs | https://docs.llamaindex.ai |
| **Haystack** | Framework de NLP com foco em busca e QA | https://haystack.deepset.ai |
| **RAGFlow** | RAG com interface visual, suporte a PDF | https://github.com/infiniflow/ragflow |

### 8.7 Validação e Schema

| Ferramenta | Uso | Link |
|---|---|---|
| **Pydantic v2** | Schema e validação do JSON de saída | https://docs.pydantic.dev |
| **RAGAS** | Avaliação automática de pipelines RAG | https://docs.ragas.io |
| **TruLens** | Monitoramento e avaliação de LLMs | https://www.trulens.org |
| **DeepEval** | Framework de testes unitários para LLMs | https://docs.confident-ai.com |

### 8.8 Interface e Deploy

| Ferramenta | Uso | Link |
|---|---|---|
| **Streamlit** | Interface rápida para MVP e painel de validação | https://docs.streamlit.io |
| **FastAPI** | API REST para integração com sistemas externos | https://fastapi.tiangolo.com |
| **Gradio** | Interface de chat com upload de arquivos | https://www.gradio.app |
| **Ollama** | Servidor local para rodar LLMs open-source | https://ollama.com |

### 8.9 Dados Geoespaciais (Futuro)

| Ferramenta | Uso | Link |
|---|---|---|
| **GeoPandas** | Leitura e análise de Shapefiles | https://geopandas.org |
| **Fiona** | I/O de formatos vetoriais (SHP, GeoJSON) | https://fiona.readthedocs.io |
| **GDAL** | Processamento de dados raster e vetor | https://gdal.org |
| **PostGIS** | Banco de dados geoespacial (futuro) | https://postgis.net |

---

## 9. Estratégia de Testes e Validação

### 9.1 Testes Automatizados

```bash
tests/
├── test_ingestor.py       # Extração e chunking de PDFs
├── test_embeddings.py     # Qualidade dos vetores gerados
├── test_retrieval.py      # Precisão do Top-K retrieval
├── test_output_schema.py  # Validação do schema JSON (Pydantic)
├── test_latencia.py       # Pipeline responde em < 5 segundos
└── test_error_handling.py # Cenários de erro e fallbacks
```

### 9.2 Benchmark Set (definido pela engenheira)

Um conjunto fixo de perguntas com **respostas esperadas** usadas para medir evolução do modelo a cada ciclo:

| # | Pergunta Exemplo | Critério de Aceite |
|---|---|---|
| 1 | "Qual pH ideal para soja no Cerrado?" | Resposta entre 6.0–6.5, cita Embrapa |
| 2 | "O que causa toxidez de alumínio no solo?" | Menciona Al³⁺, pH < 5.5, dano radicular |
| 3 | "Como calcular a necessidade de calcário?" | Menciona método SMP ou neutralização |
| 4 | "Qual a diferença entre calcário calcítico e dolomítico?" | Menciona CaO vs. CaO+MgO corretamente |
| 5 | "Quais culturas toleram solo mais ácido?" | Menciona ao menos 2 culturas com referência |

### 9.3 Métricas de Avaliação

| Métrica | Descrição | Meta MVP | Meta v2 |
|---|---|---|---|
| **Accuracy (engenheira)** | % factualmente correto | ≥ 75% | ≥ 90% |
| **Faithfulness** | Resposta baseada apenas nas fontes | ≥ 90% | ≥ 95% |
| **Coverage** | % perguntas com resposta útil | ≥ 60% | ≥ 85% |
| **Precision@5** | Chunks corretos no Top-5 | ≥ 0.70 | ≥ 0.85 |
| **Latência P95** | Tempo de resposta | < 5s | < 3s |
| **Taxa de Alucinação** | Respostas sem base documental | < 10% | < 5% |

### 9.4 Ferramentas de Avaliação RAG

- **RAGAS** — avalia `faithfulness`, `answer_relevancy`, `context_precision` automaticamente
- **TruLens** — dashboard de monitoramento contínuo de qualidade
- **DeepEval** — suite de testes unitários para LLMs (similar ao pytest)

---

## 10. Roadmap e Próximos Passos

### Fase 0 — Preparação
- [ ] Definir com a engenheira: lista de fontes de dados prioritárias da EMBRAPA e/ou outras fontes de dados relevantes
- [ ] Definir benchmark set inicial: 20–30 perguntas com respostas esperadas
- [ ] Configurar ambiente de desenvolvimento (Python 3.11+, GPU se disponível)
- [ ] Escolher LLM base para o MVP (`LLaMA 3.1 8B` via Ollama ou `GPT-4o` via API)
- [ ] Escolher VectorDB (`ChromaDB` recomendado para MVP local)

### Fase 1 — MVP RAG
- [ ] Implementar pipeline de ingestão de PDFs da EMBRAPA
- [ ] Configurar modelo de embeddings (`multilingual-e5-large`)
- [ ] Montar e popular o VectorDB com os primeiros documentos
- [ ] Implementar pipeline de query: retrieval → prompt → resposta
- [ ] Desenvolver Output Formatter com schema Pydantic
- [ ] Criar interface de chat com Streamlit (chat + upload de PDF)
- [ ] Criar painel de validação para a engenheira (Correto/Incorreto + anotação)

### Fase 2 — Avaliação e Ajustes
- [ ] Executar benchmark set com a engenheira
- [ ] Medir métricas: accuracy, faithfulness, coverage, latência
- [ ] Ajustar chunking strategy se necessário
- [ ] Implementar auto-avaliação do LLM
- [ ] Implementar tratamento de erros completo
- [ ] Adicionar Guard Classifier simples (heurística de keywords)

### Fase 3 — Fine-tuning (A partir de 200 pares validados)
- [ ] Exportar dataset `.jsonl` do Dataset Store
- [ ] Configurar pipeline de fine-tuning com PEFT + LoRA (Unsloth)
- [ ] Executar fine-tuning em GPU (local ou Google Colab A100)
- [ ] Avaliar novo modelo vs. RAG puro no benchmark set (A/B test)
- [ ] Integrar modelo fine-tuned como LLM Core (mantendo RAG para contexto)

### Fase 4 — Expansão de Fontes (Futuro)
- [ ] Conector para CSVs de laudos de análise de solo
- [ ] Conector para Shapefiles (GeoPandas)
- [ ] Conector para banco de dados PostgreSQL/PostGIS
- [ ] API REST (FastAPI) para integração com sistemas externos
- [ ] Dashboard de visualização de análises (mapas, gráficos)

---

## 11. Perguntas em Aberto

> [!IMPORTANT]
> **Infraestrutura**: O projeto rodará em nuvem (ex.: AWS) ou localmente? Isso define a escolha entre ChromaDB vs. Weaviate e LLaMA local vs. API.

> [!IMPORTANT]
> **Volume inicial**: Quantos documentos da EMBRAPA a engenheira pretende indexar na Fase 1? (10? 100? 1000 PDFs?)

> [!WARNING]
> **GPU disponível**: Fine-tuning de LLaMA 3.1 8B requer no mínimo uma GPU com 16GB VRAM (ex.: RTX 4090 ou Google Colab A100). Confirmar disponibilidade antes da Fase 3.

> [!NOTE]
> **Idioma dos documentos**: Os PDFs da EMBRAPA são em português. O modelo `multilingual-e5-large` suporta PT-BR nativamente — isso deve ser validado com um teste de recuperação inicial.

> [!NOTE]
> **Critério de volume para fine-tuning**: O threshold de 200 pares validados é uma estimativa conservadora. A engenheira pode definir um target diferente conforme a velocidade de validação.

---

## 12. Referências e Leituras Complementares

- **RAG Survey** — "Retrieval-Augmented Generation for Large Language Models: A Survey" (2023): https://arxiv.org/abs/2312.10997
- **LoRA Fine-tuning** — "LoRA: Low-Rank Adaptation of Large Language Models": https://arxiv.org/abs/2106.09685
- **RAGAS Framework** — Avaliação de pipelines RAG: https://arxiv.org/abs/2309.15217
- **LangChain RAG Tutorial**: https://python.langchain.com/docs/tutorials/rag
- **LlamaIndex RAG Guide**: https://docs.llamaindex.ai/en/stable/getting_started/concepts
- **Embrapa Solos** — Publicações técnicas: https://www.embrapa.br/solos/publicacoes
- **Embrapa Cerrado** — Boletins de Pesquisa: https://www.embrapa.br/cerrado/publicacoes

---

*Documento gerado em 14/04/2026 — TCC Análise de Solo com IA*
*Próxima revisão: após definição de infraestrutura e fontes de dados pela engenheira*
