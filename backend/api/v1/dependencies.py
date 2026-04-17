from config.settings import get_settings
from infrastructure.llm.ollama_client import get_ollama_client
from infrastructure.llm.fallback_client import get_production_llamacpp_client

def get_llm():
    """
    Retorna o BaseChatModel (LangChain) apropriado com base no ambiente.
    Injeta a dependência correta do LLM dinamicamente para as rotas do FastAPI.
    """
    settings = get_settings()
    
    if settings.ENVIRONMENT == "development":
        # Ambiente local = Ollama com GPU
        return get_ollama_client()
    else:
        # Ambiente produção = Llama.cpp servidor
        return get_production_llamacpp_client()

def get_llm_fallback():
    """
    Retorna explicitamente a instância de Fallback da Nuvem.
    Usadp apenas pelas regras de retry/contingência do CRAG.
    """
    from infrastructure.llm.fallback_client import get_fallback_client
    return get_fallback_client()
