from fastapi import FastAPI
import uvicorn
from api.v1.routes.ingestion import router as ingestion_router

app = FastAPI(title="Agronomy Assistant API", version="1.0.0")

app.include_router(ingestion_router, prefix="/api/v1/ingestion", tags=["Ingestion RAG"])

@app.get("/")
def read_root():
    return {"message": "Bem vindo a API do Sistema RAG em Python/FastAPI - Agronomy Assistant"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
