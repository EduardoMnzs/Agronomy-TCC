# Diagramas — Sistema de IA para Análise de Solo
**TCC | Atualizado em:** 14 de Abril de 2026

---

## Estrutura desta pasta

```
Diagramas/
├── mmd/          ← Código-fonte Mermaid (.mmd) — edite aqui
│   ├── 01-arquitetura-geral.mmd
│   ├── 02-fluxo-ingestao.mmd
│   ├── 03-fluxo-query.mmd
│   ├── 04-ciclo-validacao-finetuning.mmd
│   └── 05-roadmap-fases.mmd
└── svg/          ← Imagens renderizadas (.svg) — use em apresentações
    ├── 01-arquitetura-geral.svg
    ├── 02-fluxo-ingestao.svg
    ├── 03-fluxo-query.svg
    ├── 04-ciclo-validacao-finetuning.svg
    └── 05-roadmap-fases.svg
```

---

## Diagramas disponíveis

| # | Arquivo | Tipo | Descrição |
|---|---|---|---|
| 01 | `01-arquitetura-geral` | Flowchart | Visão completa das 3 camadas do sistema |
| 02 | `02-fluxo-ingestao` | Flowchart | Pipeline de ingestão de PDFs até o VectorDB |
| 03 | `03-fluxo-query` | Flowchart | Fluxo de query em tempo real com tratamento de erros |
| 04 | `04-ciclo-validacao-finetuning` | Sequence | Ciclo de validação pela engenheira e fine-tuning |
| 05 | `05-roadmap-fases` | Flowchart | Roadmap em 4 fases do projeto |

---

## Como re-renderizar após edição

```bash
# Renderizar um diagrama específico
npx @mermaid-js/mermaid-cli -i mmd/01-arquitetura-geral.mmd -o svg/01-arquitetura-geral.svg --theme dark

# Renderizar todos de uma vez (PowerShell)
$diagrams = @("01-arquitetura-geral","02-fluxo-ingestao","03-fluxo-query","04-ciclo-validacao-finetuning","05-roadmap-fases")
foreach ($d in $diagrams) {
    npx @mermaid-js/mermaid-cli -i "mmd/$d.mmd" -o "svg/$d.svg" --theme dark
}
```

## Temas disponíveis

`default` | `dark` | `forest` | `base` | `neutral`

Para temas avançados (tokyo-night, dracula, etc.) use a skill `Pretty-mermaid.md` com o pacote `beautiful-mermaid`.

---

## Visualização rápida

Abra qualquer `.mmd` no VS Code com a extensão **Mermaid Preview** ou cole o conteúdo em https://mermaid.live/
