# Guia de Comandos: Backend Agronomy Assistant (FastAPI + Celery + Qdrant + Postgres)

## Infraestrutura (Docker)

| Comando | Descrição |
| :--- | :--- |
| **`make up`** | Inicia todos os containers em background (Postgres, Redis, Qdrant) |
| **`make down`** | Para e remove os containers |
| **`make logs`** | Exibe logs dos containers em tempo real |

## Servidor (FastAPI)

| Comando | Descrição |
| :--- | :--- |
| **`make server`** | Roda o servidor FastAPI com reload automático |

## Workers (Celery + Flower)

| Comando | Descrição |
| :--- | :--- |
| **`make celery`** | Inicia o worker Celery para processamento de documentos |
| **`make celery-beat`** | Inicia o scheduler Celery (tarefas agendadas) |
| **`make flower`** | Abre o Flower (dashboard de monitoramento) no navegador |

## Banco de Dados (Postgres/Alembic)

| Comando | Descrição |
| :--- | :--- |
| **`make migrate`** | Aplica migrations pendentes no banco de dados |
| **`make migrate-new`** | Cria uma nova migration (use: `make migrate-new MSG='descrição'` ) |
| **`make migrate-history`** | Exibe histórico de migrations |
| **`make migrate-down`** | Reverte a última migration |

## Desenvolvimento

| Comando | Descrição |
| :--- | :--- |
| **`make install`** | Instala dependências do `requirements.txt` |
| **`make freeze`** | Atualiza `requirements.txt` com dependências atuais |
| **`make lint`** | Roda o linter `ruff` para checagem de código |
| **`make test`** | Executa todos os testes com `pytest` |
| **`make test-ocr`** | Testa o sistema de OCR localmente |

## Comando Master (Início Rápido)

| Comando | Descrição |
| :--- | :--- |
| **`make start`** | Inicia TUDO no mesmo terminal: Infraestrutura → Workers → Servidor |

## Ver Todos os Comandos

```bash
make help
```