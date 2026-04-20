import json
import logging
import httpx
from typing import Dict, Any
from config.settings import get_settings
import fitz
import pandas as pd

logger = logging.getLogger(__name__)
settings = get_settings()


class MetadataExtractorAgent:
    """
    Agente LLM que lê um trecho amostral de arquivos recém-chegados para extrair metadados vitais.
    """

    def __init__(self):
        self.llm_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model = settings.LLM_MODEL

    def _get_document_sample(self, file_path: str) -> str:
        """Puxa uma amostra (primeiras linhas ou página 1) do arquivo fisico."""
        if file_path.endswith(".pdf"):
            try:
                doc = fitz.open(file_path)
                text = doc[0].get_text("text") if len(doc) > 0 else ""
                doc.close()
                return text[:1000]
            except FileNotFoundError:
                logger.error(f"Arquivo não encontrado para amostragem: {file_path}")
                return ""
            except Exception as e:
                logger.warning(f"Falha ao extrair amostra do PDF '{file_path}': {e}")
                return ""
        elif file_path.endswith(".csv"):
            try:
                df = pd.read_csv(file_path, nrows=5)
                return df.to_csv(index=False)
            except FileNotFoundError:
                logger.error(f"Arquivo não encontrado para amostragem: {file_path}")
                return ""
            except Exception as e:
                logger.warning(f"Falha ao extrair amostra do CSV '{file_path}': {e}")
                return ""
        return ""

    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrai as propriedades mágicas via LLM retornando JSON preenchido."""
        amostra = self._get_document_sample(file_path)

        prompt = f"""Você é um extrator de metadados agronômicos. Seu único papel é retornar um JSON válido.

        REGRAS DE EXTRAÇÃO:
        - "titulo": Extraia o título exato do documento. Se não for óbvio, crie um com no máximo 5 palavras.
        - "orgao_emissor": Instituição ou empresa (Ex: Embrapa, MAPA, Syngenta). Se não encontrar, use "Desconhecido".
        - "categoria_agronomica": ESCOLHA ESTritamente UMA DESTAS OPÇÕES: ["Solos", "Defensivos", "Sementes", "Clima", "Maquinário", "Geral"]. Não invente categorias.

        TEXTO PARA ANÁLISE:
        ---
        {amostra}
        ---

        Responda APENAS com o JSON, sem formatação markdown ou explicações. Use exatamente este formato:
        {{
        "titulo": "",
        "orgao_emissor": "",
        "categoria_agronomica": ""
        }}"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.llm_url, json=payload)
                response.raise_for_status()
                data = response.json()
                result_text = data.get("response", "{}")
                metadata = json.loads(result_text)

                return {
                    "titulo": metadata.get("titulo") or "Documento Sem Titulo",
                    "orgao_emissor": metadata.get("orgao_emissor") or "Desconhecido",
                    "categoria_agronomica": metadata.get("categoria_agronomica")
                    or "Geral",
                    "tipo_documento": "PDF" if file_path.endswith(".pdf") else "CSV",
                    "status_processamento": "PENDENTE",
                    "caminho_temporario": file_path,
                }
        except Exception as e:
            logger.warning(
                f"Ollama indisponível ({e}). Tentando Fallback para LLAMA_CPP_BASE_URL..."
            )
            fallback_url = f"{settings.LLAMA_CPP_BASE_URL}/chat/completions"
            fallback_payload = {
                "model": settings.LLAMA_CPP_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": """Você é um bot catalogador de dados agronômicos. O seu ÚNICO papel é responder com um JSON perfeitamente válido. Não adicione explicações ou formato markdown.
Deduza os metadados com base no texto lido e aplique estas REGRAS VITAIS:
- "titulo": O título principal e mais descritivo do documento.
- "orgao_emissor": O instituto, ministério ou empresa. Ex: Embrapa, MAPA, Syngenta, Jacto. Se não encontrar, preencha com "Desconhecido".
- "categoria_agronomica": O tema raiz do documento. Ex: "Análise de Solo", "Defensivos", "Genética e Sementes", "Maquinário", "Clima". Se não achar óbvio, deduza o mais correto.

Formato OBRIGATÓRIO de saída:
{"titulo": "nome do doc", "orgao_emissor": "instituicao", "categoria_agronomica": "tema principal"}""",
                    },
                    {
                        "role": "user",
                        "content": f"Extraia metadados estritos da amostra:\n\n{amostra}",
                    },
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 300,
                "temperature": 0.1,
            }
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp_fb = await client.post(fallback_url, json=fallback_payload)
                    resp_fb.raise_for_status()
                    data_fb = resp_fb.json()

                    choice = data_fb.get("choices", [{}])[0]
                    content = choice.get("message", {}).get("content", "{}")

                    logger.debug(
                        f"[{settings.LLAMA_CPP_MODEL}] Conteúdo bruto retornado:\n{content}\n---"
                    )

                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    elif content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()

                    if not content.endswith("}"):
                        content = content + "\n}"

                    metadata = json.loads(content)
                    return {
                        "titulo": metadata.get("titulo")
                        or "Documento Sem Titulo (Fallback)",
                        "orgao_emissor": metadata.get("orgao_emissor")
                        or "Desconhecido",
                        "categoria_agronomica": metadata.get("categoria_agronomica")
                        or "Geral",
                        "tipo_documento": "PDF"
                        if file_path.endswith(".pdf")
                        else "CSV",
                        "status_processamento": "PENDENTE",
                        "caminho_temporario": file_path,
                    }
            except Exception as ex_fb:
                logger.error(
                    f"Fallback LLM também falhou: {ex_fb}. Aplicando metadados padrão."
                )
            return {
                "titulo": "Documento Rascunho",
                "orgao_emissor": "Indefinido",
                "categoria_agronomica": "Geral",
                "tipo_documento": "PDF" if file_path.endswith(".pdf") else "CSV",
                "status_processamento": "PENDENTE",
                "caminho_temporario": file_path,
            }
