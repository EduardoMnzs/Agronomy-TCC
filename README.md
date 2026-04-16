# Sistema de IA para Análise de Prescrições Agronômicas

> TCC — Assistente Inteligente para Análise de Prescrições Agronômicas a partir de Documentos Técnicos

**Autor:** Eduardo Menezes  
**Data de início:** Abril de 2026  
**Status:** Planejamento e Prototipagem Inicial

---

## Sobre o Projeto

Este projeto desenvolve um **sistema de inteligência artificial** capaz de responder perguntas técnicas sobre análise de prescrições agronômicas, com base em documentos técnicos (PDFs de fonte como a EMBRAPA) e dados de campo (planilhas, shapefiles, laudos).

A ideia central é transformar um vasto acervo de literatura técnica dispersa em um **assistente conversacional especializado**, auditável e em constante melhora — validado por uma engenheira agrônoma especialista.

### O que o sistema faz

- Ingere PDFs técnicos e os transforma em base de conhecimento pesquisável
- Responde perguntas em linguagem natural sobre solo, culturas e recomendações
- Analisa arquivos de dados de solo enviados pelo usuário (CSVs, planilhas, shapefiles)
- Exporta respostas em dois formatos: **chat conversacional** e **JSON estruturado**
- Aprende continuamente a partir das validações da engenheira agrônoma

---

## Arquitetura (Resumo)

O sistema é baseado na abordagem híbrida **RAG + Fine-tuning**:

```
PDFs → Extração → Chunking → Embeddings → VectorDB
                                              ↓
Pergunta → Guard Classifier → Retrieval → LLM → Auto-avaliação → Resposta
                                                                      ↓
                                              Engenheira valida → Dataset Store
                                                                      ↓
                                              N ≥ 200 pares → Fine-tuning → Modelo v2
```

**Fases de evolução:**

| Fase       | Descrição                           | Tecnologia Central         |
| ---------- | ----------------------------------- | -------------------------- |
| **Fase 0** | Preparação e definição de fontes    | —                          |
| **Fase 1** | MVP com RAG puro                    | LangChain + ChromaDB + LLM |
| **Fase 2** | Avaliação e ajustes com engenheira  | RAGAS + DeepEval           |
| **Fase 3** | Fine-tuning com pares validados     | PEFT + LoRA + Unsloth      |
| **Fase 4** | Expansão para Shapefiles, CSVs, API | GeoPandas + FastAPI        |

---

## Estrutura do Projeto

```
TCC/
├── README.md                              ← Este arquivo
│
├── Relatório de Progresso/
│   └── relatorio 14-04 - Planejamento Inicial.md   ← Documento completo de planejamento
│
├── Diagramas/
│   ├── README.md                          ← Como usar e re-renderizar
│   ├── mmd/                               ← Código-fonte Mermaid (editável)
│   │   ├── 01-arquitetura-geral.mmd
│   │   ├── 02-fluxo-ingestao.mmd
│   │   ├── 03-fluxo-query.mmd
│   │   ├── 04-ciclo-validacao-finetuning.mmd
│   │   └── 05-roadmap-fases.mmd
│   └── svg/                               ← Diagramas renderizados (para apresentações)
│       ├── 01-arquitetura-geral.svg
│       ├── 02-fluxo-ingestao.svg
│       ├── 03-fluxo-query.svg
│       ├── 04-ciclo-validacao-finetuning.svg
│       └── 05-roadmap-fases.svg
│
├── Prescrição/                            ← Dados reais de campo (Shapefiles, CSVs, laudos)
│   └── Agro Lagoa da Prata/
│       ├── 2024/                          ← Análises e prescrições 2024
│       └── 2025/                          ← Análises e prescrições 2025
│           ├── ANALISE/                   ← Shapefile de análise de prescrições agronômicas
│           ├── CONTORNO/                  ← Shapefile de contorno da área
│           ├── FERTILIZANTES E CORRETIVOS/
│           └── MAPAS_DOSE/ e MAPAS_FERTILIDADE/
│
└── .claude/
    └── skills/                            ← Skills de desenvolvimento
        ├── Brainstorming.md
        └── Pretty-mermaid.md
```

---

## Diagramas

| #   | Diagrama                         | Visualizar                                                                                                       |
| --- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 01  | Arquitetura Geral do Sistema     | [SVG](Diagramas/svg/01-arquitetura-geral.svg) \| [MMD](Diagramas/mmd/01-arquitetura-geral.mmd)                   |
| 02  | Fluxo de Ingestão de Documentos  | [SVG](Diagramas/svg/02-fluxo-ingestao.svg) \| [MMD](Diagramas/mmd/02-fluxo-ingestao.mmd)                         |
| 03  | Fluxo de Query em Tempo Real     | [SVG](Diagramas/svg/03-fluxo-query.svg) \| [MMD](Diagramas/mmd/03-fluxo-query.mmd)                               |
| 04  | Ciclo de Validação e Fine-tuning | [SVG](Diagramas/svg/04-ciclo-validacao-finetuning.svg) \| [MMD](Diagramas/mmd/04-ciclo-validacao-finetuning.mmd) |
| 05  | Roadmap por Fases                | [SVG](Diagramas/svg/05-roadmap-fases.svg) \| [MMD](Diagramas/mmd/05-roadmap-fases.mmd)                           |

> Para re-renderizar após editar um `.mmd`:
>
> ```bash
> npx @mermaid-js/mermaid-cli -i Diagramas/mmd/01-arquitetura-geral.mmd -o Diagramas/svg/01-arquitetura-geral.svg --theme dark
> ```

---

## Tecnologias Principais

### Processamento de Documentos

- **PyMuPDF / pdfplumber** — extração de texto de PDFs
- **LangChain** — pipeline de ingestão e chunking semântico
- **LlamaIndex** — framework RAG alternativo

### Embeddings e Busca Vetorial

- **multilingual-e5-large** — modelo de embeddings com suporte a PT-BR
- **ChromaDB** (MVP) / **Weaviate** (cloud) — banco vetorial

### Modelos de Linguagem (LLM)

- **LLaMA 3.1 8B** (local, via Ollama) — para privacidade e fine-tuning
- **GPT-4o / Gemini 1.5 Pro** (API) — para qualidade máxima no MVP

### Fine-tuning

- **Hugging Face PEFT + LoRA** — adaptação eficiente de parâmetros
- **Unsloth** — fine-tuning 2x mais rápido com menos VRAM

### Interface e API

- **Streamlit** — interface de chat e painel de validação (MVP)
- **FastAPI** — API REST para integração externa (v2)
- **Pydantic v2** — schema e validação do JSON de saída

### Dados Geoespaciais (Fase 4)

- **GeoPandas** — leitura de Shapefiles
- **PostGIS** — banco geoespacial

### Avaliação

- **RAGAS** — métricas automáticas de pipelines RAG
- **DeepEval** — testes unitários para LLMs
- **TruLens** — monitoramento contínuo

---

## Saída do Sistema

O sistema retorna respostas em dois formatos simultâneos:

**Chat** — linguagem natural com citação de fonte  
**JSON** — estruturado para integração com outros sistemas

```json
{
  "resposta": "Solo ácido com pH 5.2, recomenda-se calagem.",
  "confianca": 0.87,
  "fontes": [
    { "titulo": "Embrapa Cerrado - Boletim Técnico 42", "pagina": 18 }
  ],
  "parametros_solo": { "pH": 5.2, "fosforo_ppm": null, "potassio_cmolc": null },
  "cultura_alvo": "soja",
  "regiao": "Cerrado",
  "recomendacoes": [
    {
      "tipo": "calagem",
      "prioridade": "alta",
      "quantidade_estimada": "2.5 t/ha"
    }
  ],
  "nivel_alerta": "moderado",
  "flags": ["solo_acido", "risco_toxidez_aluminio"],
  "qualidade": {
    "confianca": 0.87,
    "requer_validacao": false,
    "validado_por_especialista": false
  }
}
```

---

## Documentação

| Documento                                                                                                         | Descrição                                                                   |
| ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| [Relatório de Planejamento Inicial](Relatório%20de%20Progresso/relatorio%2014-04%20-%20Planejamento%20Inicial.md) | Planejamento completo: arquitetura, ferramentas, fluxos, métricas e roadmap |
| [README dos Diagramas](Diagramas/README.md)                                                                       | Como editar e re-renderizar os diagramas Mermaid                            |

---

## Dados de Campo Disponíveis

A pasta `Prescrição/` contém dados reais de campo da **fazenda Agro Lagoa da Prata**:

- Shapefiles de análise de prescrições agronômicas (`ANALISE/*.shp`)
- Shapefiles de contorno de área (`CONTORNO/*.shp`)
- Mapas de fertilidade (Ca, Mg, K, P, CTC, V%)
- Mapas de prescrição de dose de fertilizantes e corretivos
- Receitas agronômicas e resumos em CSV

Esses dados serão utilizados como **base de validação** e **caso de uso real** do sistema a partir da Fase 4.

---

## Próximos Passos Imediatos

- [ ] Definir com a engenheira as fontes de dados prioritárias
- [ ] Criar benchmark set com 20–30 perguntas de referência e respostas esperadas
- [ ] Configurar ambiente Python 3.11+ e escolher LLM base
- [ ] Implementar pipeline de ingestão de PDFs (Fase 1)

---

_TCC — Sistema de IA para Análise de Prescrições Agronômicas | Iniciado em Abril de 2026_
