from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from config.settings import get_settings
from infrastructure.llm.base import LLMProvider
import warnings

def get_production_llamacpp_client() -> ChatOpenAI:
    settings = get_settings()
    # O Llama.cpp remoto expõe uma API compatível com OpenAI
    return ChatOpenAI(
        api_key="sk-no-key",  # Dummy key, ignorada pelo llama.cpp
        base_url=settings.LLAMA_CPP_BASE_URL,
        model=settings.LLAMA_CPP_MODEL,
        temperature=0.0,
        max_retries=1
    )

def get_fallback_client():
    settings = get_settings()
    provider = settings.FALLBACK_LLM_PROVIDER.lower()
    
    if not settings.FALLBACK_API_KEY or settings.FALLBACK_API_KEY == "sua_chave_aqui":
        warnings.warn("FALLBACK_API_KEY nao foi declarada corretamente no .env!")

    if provider == LLMProvider.OPENAI.value:
        return ChatOpenAI(
            api_key=settings.FALLBACK_API_KEY,
            model=settings.FALLBACK_MODEL_NAME,
            temperature=0.0
        )
    elif provider == LLMProvider.GOOGLE.value:
        return ChatGoogleGenerativeAI(
            api_key=settings.FALLBACK_API_KEY,
            model=settings.FALLBACK_MODEL_NAME,
            temperature=0.0
        )
    elif provider == LLMProvider.ANTHROPIC.value:
        return ChatAnthropic(
            api_key=settings.FALLBACK_API_KEY,
            model=settings.FALLBACK_MODEL_NAME,
            temperature=0.0
        )
    else:
        raise ValueError(f"Provedor de fallback '{provider}' nao suportado.")
