# Inicialização do Backend

Este documento descreve como inicializar e configurar o ambiente de desenvolvimento do backend (Agronomy Assistant) recém estruturado.

## 1. Estrutura do Projeto
A arquitetura do projeto foi estruturada baseando-se no padrão **Clean Architecture (Ports & Adapters)** conforme definido.
Todas as pastas propostas (api, core, infrastructure, config, prompts, workers) foram criadas na pasta `backend/`.

## 2. Preparando o Ambiente (Local)

Na pasta `backend/`:

1. **Crie o ambiente virtual:**
   ```bash
   py -m venv venv
   ```

2. **Ative o ambiente virtual:**
   - No Windows: `.\venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   *Nota: Pode demorar um pouco para instalar dependências pesadas como `sentence-transformers` e pacotes do vetor.*

## 3. Rodando o Servidor Localmente

Um arquivo `main.py` de inicialização (MVP) já foi criado usando FastAPI.

Ative o ambiente e inicie o servidor:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Isso publicará a API em:
- Documentação interativa: http://127.0.0.1:8000/docs
- Hello World: http://127.0.0.1:8000/