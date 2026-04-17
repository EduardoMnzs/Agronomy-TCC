# Design: Cliente de LLM Híbrido (Ollama + Llama.cpp)

**Data:** 16/04/2026
**Versão:** 1.0
**Status:** Implementado

## Sumário
Este design detalha a arquitetura do cliente de IA generativa para o backend do Agronomy Assistant, focado em entregar inferência através de dois ambientes paralelos para desenvolvimento e produção, mitigando custos e garantindo aderência à infraestrutura da faculdade. A estratégia híbrida utiliza a facilidade do Ollama local e a estabilidade do servidor llama.cpp remoto.

## Arquitetura
O design aplica o princípio "Strategy" (ou Factory) via injeção de dependência na Clean Architecture. O resto do aplicativo não conversará diretamente com a API do Ollama e nem Llama.cpp. Eles dialogarão com uma classe abstrata comum (ports), enquanto a camada de infraestrutura define as opções que cumprem as exigências usando bibliotecas correspondentes.

## Componentes
1. **`LLMClientBase` (`infrastructure/llm/base.py`)**
   Interface/Classe base abstrata declarando o método de inferência, como `.agenerate_chat(...)`.
2. **`OllamaClient` (`infrastructure/llm/ollama_client.py`)**
   Classe que usa o cliente do pacote `ollama` para falar diretamente com `localhost:11434` em tempo de desenvolvimento. 
3. **`FallbackLLMClient` (`infrastructure/llm/fallback_client.py`)**
   Substitui o `FallbackLLMClient` de fallback rígido. Utiliza as bibliotecas do LangChain (`ChatOpenAI`, `ChatAnthropic`, `ChatGoogleGenerativeAI`) para selecionar dinamicamente a nuvem a ser utilizada baseada na variável do ambiente `FALLBACK_LLM_PROVIDER`. Caso o llama.cpp do servidor caia, a requisição transiciona com segurança independentemente se a nuvem for OpenAI, Gemini ou Claude.
4. **`Dependencies` (`api/v1/dependencies.py`)**
   Sabe ler do `.env` se está rodando local (`ENVIRONMENT=development`) para instanciar o `OllamaClient`, ou produção (`ENVIRONMENT=production`) para instanciar o `FallbackLLMClient`.

## Fluxo de Dados
1. Recebimento da query do agricultor pelo endpoint do FastAPI.
2. Recuperação vetorial RAG completada.
3. FastAPI invoca o LLM injetado através do `Dependencies`.
4. Em *desenvolvimento*: A requisição vai por rede local para `Ollama (GPU)`.
5. Em *produção*: A requisição viaja pela internet convertida via JSON contendo endpoint `/v1/chat/completions` em `llama.labs.unimar.br`.
6. Resposta encapsulada no modelo pydantic de saída.

## Tratamento de Erros
- **Server Offline:** Ambos os clientes englobam lógicas locais de timeout. Quando `LLM_UNAVAILABLE` é engatilhado no LLama.cpp, o `FallbackLLMClient` imediatamente transiciona para usar o modelo de fallback configurado.
- **Rate Limit Local:** Ollama não tem limites, mas o Llama.cpp enfileirará até 24 workers. Passou desta conta? Transiciona para modelo de fallback momentâneo.

## Estratégia de Testes
- Utilização de `pytest-mock` para validar fallback caso a infraestrutura da Unimar fique inacessível ou o LLaMA no Portainer falhe.
- `unittest` local validando a interface abstrata garantindo que tanto `OllamaClient` quanto o `FallbackLLMClient` retornam os dicionários no mesmo padrão que será aceito pelo LangGraph.

## Questões em Aberto
- Nenhum momento crítico não resolvido no desenvolvimento inicial desta factory. Caso o roteador LangGraph force tool calls (chamadas de ferramenta) atípicas no futuro, analisaremos se o LLaMA-Instruct suportará chamadas formatadas localmente.

---

*Implementado em 16/04/2026 — Sistema de IA para Análise de Prescrições Agronômicas*
