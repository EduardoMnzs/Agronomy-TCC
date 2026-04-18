# Relatório Técnico — Brainstorming Arquitetura Híbrida e Validação de Rastreabilidade

**Data:** 18 de Abril de 2026  
**Projeto:** TCC — Assistente Inteligente para Análise de Prescrições Agronômicas
**Sessão:** Backend RAG: Persistência Poliglota, Catálogos e Benchmarking de Ingestão

---

## 1. Objetivo

Ajustar e redefinir a base arquitetural de persistência e orquestração do Agronomy Assistant, resolvendo preocupações de rastreabilidade levantadas na reunião com o pesquisador Bruno Callegaro (Jacto). O foco principal é blindar o RAG contra alucinações matemáticas e garantir a comprovação auditável (citação exata da fonte) no retorno das respostas.

**Justificativa:** No domínio agronômico, respostas devem possuir validação científica inquestionável. Depender unicamente de buscas semânticas em linguagem natural para cruzar dados exatos (códigos da API Zarc, doses) ou geográficos (Shapefiles) abre uma grande margem para a geração de prescrições errôneas e danosas à lavoura.

---

## 2. Decisões Arquiteturais

### 2.1 Persistência Poliglota (Desmembramento de Bancos)
O projeto abandonou a premissa engessada de um único banco (Qdrant) recebendo toda a ingestão como texto. Agora, as diferentes naturezas de dados passam a habitar bases especializadas:

```text
Se o arquivo possui linguagem livre/não-estruturada (PDFs/Bulas) → Qdrant (Vetorial)
Se o dado é fixo, tabular e derivado de API (CSV/Zarc/Embrapa) → PostgreSQL (Relacional)
Se a informação é um contorno territorial de campo (SHP) → PostGIS (Espacial)
```

### 2.2 O Orquestrador Inteligente
Em vez do sistema RAG operar linearmente, será acoplado o **LangGraph** atuando como um *Query Router*. Este Agente Orquestrador atuará antes de qualquer pesquisa: primeiro ele entende a intenção da pergunta e age como o "Maestro", selecionando qual Banco Especializado acessar via filtragem restrita nos embeddings ou chamadas Text-To-SQL.

---

## 3. Stack Utilizada (Ingestão)

| Tecnologias Base | Finalidade |
|---|---|
| **LangGraph** | Roteamento Inteligente (*Query Routing*) e Orquestração de Agentes |
| **Qdrant DB** | Persistência restrita de Textos Semânticos / Manuais |
| **PostgreSQL** | Cálculos estritos (Text-to-SQL) e Repositório do Catálogo de Metadados |
| **PostGIS** | Extensão nativa do Postgres habilitada para cruzamentos da cartografia (.SHP) |

---

## 4. O Sistema de Rastreabilidade

### 4.1 O problema
As engines RAG clássicas vetorizam dados brutos de PDF onde as rotinas frequentemente perdem do que o bloco trata, permitindo ao LLM inferir equivocadamente e exibir laudos sem vínculo comprobatório irrefutável com os dados submetidos pelo agronegócio.

### 4.2 Solução: Catálogo e Parsers no Ingestion Worker
Estabeleceu-se uma **Taxonomia de Restrição Absoluta**. 
O Celery agora fragmentará o controle da ingestão usando "Parsers Analíticos" nativos e independentes. **Nenhum chunk** persistirá nos bancos se não carregar o preenchimento obrigatório da tag `id_fonte` e `coordenada_local`.
Concomitantemente, criou-se a tabela mestre `CatalogoFontes` no PostgreSQL para guardar atributos puramente textuais e organizacionais da fonte. A busca usará apenas a ID blindada numéricamente; contudo, o front-end montará a citação perfeita via um *LookUp* limpo nests metadados puramente relacionais.

---

## 5. Prevenção de Alucinação

### 5.1 O Problema
Depender do LLM compor as saídas conversacionais para checar empiricamente se ele inventou uma métrica do "Milho" é inescalável. O problema precisava ser estrangulado no *Retrieval*.

### 5.2 Correção via Benchmarking Matemático
Aplicaremos testes exaustivos focados tão somente no módulo "Information Retrieval" (Busca & Extração). 
- Construção manual imediata de um gabarito contendo perguntas atípicas e suas fontes inquestionáveis, atestadas pela área agronômica (O *Ground Truth Dataset*).
- Geração de automações métricas analisando NDCG/MRR (Posicionamento de Busca).
- Um teste passa a ser condecorado válido apenas se a fonte exata e referenciada repousar rigorosamente entre os **`TOP 3`** primeiros documentos recuperados pelo *Agente Orquestrador*.

---

## 6. Resultado Final

O *Agronomy Assistant* sofre alteração de rota, saindo da categoria conceitual de RAG Vetorial para **Agentic RAG com Persistência Poliglota Corporativa**.
*   Processos isolados impedem o vazamento espacial com cruzamentos irresponsáveis de semântica natural.
*   Extração imune à contaminação de embeddings com supressão estética transferida à *Catálogos*.
*   Métrica 100% de confiabilidade de fonte impulsionando viabilidade comercial/científica do produto.

---

## 7. Lições Aprendidas e Padrões Estabelecidos

| Situação | Problema | Padrão Correto |
|---|---|---|
| **Arquivos CSV/SHP vetorizados em Textos** | Impossível fazer cálculo matemático ou de raios geográficos | **Bancos Híbridos.** Roteio para uso de linguagem SQL e módulos puramente de `PostGIS` |
| **Validação da Citação Científica** | A IA infere números de página por si ou se confunde | Implementar **Parsers Estritos no Celery** que bloqueiam dados carentes de ID no Payload |
| **Teste da Recuperação RAG** | Indistinção entre a Geração ruim e a Recuperação ruim | Desacoplar medições; usar `Ground Truth Dataset` com avaliação severa de IR (Método MRR/NDCG) |

---

## 8. Atualização do Stack Técnico

Os atributos e caminhos arquiteturais receberam validações definitivas de re-engenharia:

| Item | Planejado Originalmente | Corrigido/Confirmado |
|---|---|---|
| **Base dados CSV estruturada** | Extração textual com injeções em Qdrant | **PostgreSQL** para manuseios numéricos |
| **Geometria / ShapeFile** | Não previsto centralmente | **PostGIS DB** |
| **Orquestrador Decisório** | Cadeia de Prompt LangChain com Guard-Rails | Agentes Múltiplos e Roteamento via **LangGraph** |

---

## 9. Próximos Passos (Infraestrutura Lógica)

- [ ] Incorporar Container Docker portando imagens limpas PostgreSQL e módulos PostGIS ao compose da infraestrutura
- [ ] Refatoração do `ingestion_worker.py` integrando 'Parsers Estritos' como Filtros Obrigatórios de Ingestão
- [ ] Criar no repositório backend os "Models" SQLAlchemy que gerarão as tabelas `CatalogoFontes` automaticamente
- [ ] Formulação laboratorial com a coordenação de Engenharia Agrícola do "Ground Truth Dataset" de amostras alvo
- [ ] Programação dos Nós Roteadores Principais `Router Agent` usando `LangGraph`

---

*Documento gerado em 18/04/2026 — TCC Análise de Prescrições Agronômicas com IA*
