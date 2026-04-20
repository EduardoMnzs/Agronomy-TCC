from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Ambiente
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Agronomy Assistant"
    
    # Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1"
    
    # Llama.cpp Servidor
    LLAMA_CPP_BASE_URL: str = "https://llama.labs.unimar.br/v1"
    LLAMA_CPP_MODEL: str = "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"
    
    # Fallback LLM Dinâmico
    FALLBACK_LLM_PROVIDER: str = "openai"
    FALLBACK_API_KEY: str | None = None
    FALLBACK_MODEL_NAME: str = "gpt-4o-mini"
    
    # LlamaParse (fallback premium de extração PDF)
    LLAMAPARSE_API_KEY: str | None = None

    # Message Broker e Celery Backbone
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Banco de Dados Relacional (PostgreSQL)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "agronomy"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5433
    
    @property
    def POSTGRES_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache()
def get_settings():
    return Settings()
