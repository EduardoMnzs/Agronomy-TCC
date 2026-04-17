from langchain_community.chat_models import ChatOllama
from config.settings import get_settings

def get_ollama_client() -> ChatOllama:
    settings = get_settings()
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0.0  # Zero para garantir determinismo no Agent
    )
