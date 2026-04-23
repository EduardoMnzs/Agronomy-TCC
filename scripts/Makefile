.PHONY: help up down logs shell migrate migrate-new migrate-history \
        server celery celery-beat flower install freeze lint test start

BACKEND=../backend
VENV_BIN=venv\Scripts
PYTHON=$(BACKEND)\$(VENV_BIN)\python
UVICORN=$(BACKEND)\$(VENV_BIN)\uvicorn
CELERY=$(BACKEND)\$(VENV_BIN)\celery
ALEMBIC=$(BACKEND)\$(VENV_BIN)\alembic

help:
	@echo ""
	@echo "  INFRAESTRUTURA"
	@echo "  up           Sobe todos os containers (Postgres, Redis, Qdrant)"
	@echo "  down         Para e remove os containers"
	@echo "  logs         Exibe logs dos containers em tempo real"
	@echo ""
	@echo "  SERVIDOR"
	@echo "  server       Roda o servidor FastAPI (uvicorn)"
	@echo ""
	@echo "  WORKERS"
	@echo "  celery       Roda o worker Celery de ingestão"
	@echo "  celery-beat  Roda o Celery Beat (tarefas agendadas)"
	@echo "  flower       Abre o Flower para monitorar filas"
	@echo "  start        Inicia TUDO (Docker + Server + Workers) em novas janelas"
	@echo ""
	@echo "  BANCO DE DADOS"
	@echo "  migrate      Aplica as migrations pendentes"
	@echo "  migrate-new  Gera nova migration (uso: make migrate-new MSG='descricao')"
	@echo "  migrate-history  Exibe histórico de migrations"
	@echo "  migrate-down Reverte a última migration"
	@echo ""
	@echo "  DESENVOLVIMENTO"
	@echo "  install      Instala dependências do requirements.txt"
	@echo "  freeze       Atualiza requirements.txt com dependências atuais"
	@echo "  lint         Roda ruff para checar o código"
	@echo "  test         Roda os testes com pytest"
	@echo "  test-ocr     Roda o script de teste de OCR local"
	@echo ""

# --- Infraestrutura ---

up:
	docker compose -f $(BACKEND)/docker-compose.yml up -d

down:
	docker compose -f $(BACKEND)/docker-compose.yml down

logs:
	docker compose -f $(BACKEND)/docker-compose.yml logs -f

# --- Servidor ---

server:
	cd $(BACKEND) && .\$(VENV_BIN)\uvicorn main:app --reload --host 0.0.0.0 --port 8000

# --- Workers ---

celery:
	cd $(BACKEND) && .\$(VENV_BIN)\celery -A workers.celery_app worker --loglevel=info -Q ingestion --pool=solo

celery-beat:
	cd $(BACKEND) && .\$(VENV_BIN)\celery -A workers.celery_app beat --loglevel=info

flower:
	cd $(BACKEND) && .\$(VENV_BIN)\celery -A workers.celery_app flower --port=5555

# --- Banco de Dados ---

migrate:
	cd $(BACKEND) && .\$(VENV_BIN)\alembic upgrade head

migrate-new:
	cd $(BACKEND) && .\$(VENV_BIN)\alembic revision --autogenerate -m "$(MSG)"

migrate-history:
	cd $(BACKEND) && .\$(VENV_BIN)\alembic history --verbose

migrate-down:
	cd $(BACKEND) && .\$(VENV_BIN)\alembic downgrade -1

# --- Desenvolvimento ---

install:
	cd $(BACKEND) && .\$(VENV_BIN)\python -m pip install -r requirements.txt

freeze:
	cd $(BACKEND) && .\$(VENV_BIN)\python -m pip freeze > requirements.txt

lint:
	cd $(BACKEND) && .\$(VENV_BIN)\ruff check .

test:
	cd $(BACKEND) && .\$(VENV_BIN)\pytest -v

test-ocr:
	cd $(BACKEND) && .\$(VENV_BIN)\python scripts\test_local_ocr.py

# --- Master Start ---

start: up
	@echo "Iniciando todos os servicos no mesmo terminal..."
	$(PYTHON) start_all.py
