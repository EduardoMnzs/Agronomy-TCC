import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.v1.dependencies import get_llm, get_llm_fallback
from config.settings import get_settings

def test():
    settings = get_settings()
    print("Provider configurado:", settings.FALLBACK_LLM_PROVIDER)
    
    try:
        llm = get_llm()
        print("Modelo primario instanciado:", type(llm).__name__)
    except Exception as e:
        print("ERRO Primario:", str(e))

    try:
        fallback = get_llm_fallback()
        print("Modelo fallback instanciado:", type(fallback).__name__)
    except Exception as e:
        print("ERRO Fallback:", str(e))

if __name__ == "__main__":
    test()
