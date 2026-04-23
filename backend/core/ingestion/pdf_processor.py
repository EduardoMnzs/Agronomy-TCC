"""
PDFProcessor: Chain of Responsibility para extração de PDFs agronômicos.

Fluxo:
  1. LocalParserNode   — PyMuPDF (gratuito, zero latência de rede)
  2. LLMValidatorNode  — LLM local (Ollama) mapeia texto → ExtractionResult Pydantic
                          com até MAX_RETRIES tentativas em ValidationError
  3. LlamaParseNode    — fallback premium, instanciado apenas se o validador exaurir
                          retries (Lazy Loading para evitar cold start)

O Qdrant nunca sabe qual nó gerou o documento: tudo sai como
langchain_core.documents.Document com metadado `extraction_node` para métricas.
"""

import re
import json
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Dict, Set, Tuple, Optional

import fitz
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from core.ingestion.schemas import ExtractionResult, ExtractionQuality

logger = logging.getLogger(__name__)

_OCR_THRESHOLD = 50
_TABLE_BODY_MAX_GAP = 12.0
MAX_RETRIES = 2

# OCR helper (lazy, mantido fora das classes para reuso cross-node)
@lru_cache(maxsize=1)
def _get_ocr_reader():
    try:
        import easyocr
        reader = easyocr.Reader(["pt", "en"], gpu=False, verbose=False)
        logger.info("EasyOCR carregado.")
        return reader
    except ImportError:
        logger.warning("easyocr não instalado — OCR indisponível.")
        return None
    except Exception as e:
        logger.error(f"Falha ao inicializar EasyOCR: {e}")
        return None


def _ocr_page(page: fitz.Page) -> str:
    reader = _get_ocr_reader()
    if reader is None:
        return ""
    try:
        mat = fitz.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        img_bytes = pix.tobytes("png")
        import numpy as np
        from PIL import Image
        import io
        img = np.array(Image.open(io.BytesIO(img_bytes)))
        return "\n".join(reader.readtext(img, detail=0, paragraph=True))
    except Exception as e:
        logger.warning(f"OCR falhou na página: {e}")
        return ""

# Funções de parsing de tabelas
def _clean_text(text: str) -> str:
    text = re.sub(r"[^\S\n\t ]+", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line for line in text.splitlines() if line.strip())
    return text.strip()


def _table_header_to_markdown(table) -> str:
    rows = table.extract()
    if not rows:
        return ""

    def cell(v) -> str:
        return str(v).strip() if v is not None else ""

    md_lines = []
    for row in rows:
        md_lines.append("| " + " | ".join(cell(c) for c in row) + " |")
        if len(md_lines) == 1:
            md_lines.append("| " + " | ".join("---" for _ in row) + " |")
    return "\n".join(md_lines)


def _collect_table_body(
    page: fitz.Page,
    header_bbox: fitz.Rect,
    all_blocks: list,
) -> Tuple[str, Set[int]]:
    candidates = [
        (i, b) for i, b in enumerate(all_blocks)
        if b[1] >= header_bbox.y1 - 5
        and b[0] <= header_bbox.x1 + 15
        and b[2] >= header_bbox.x0 - 15
    ]
    candidates.sort(key=lambda x: x[1][1])

    body_lines: List[str] = []
    consumed: Set[int] = set()
    prev_y1 = header_bbox.y1

    for idx, block in candidates:
        gap = block[1] - prev_y1
        if gap > _TABLE_BODY_MAX_GAP:
            break
        cells = [c.strip() for c in block[4].strip().splitlines() if c.strip()]
        if cells:
            body_lines.append("| " + " | ".join(cells) + " |")
        consumed.add(idx)
        prev_y1 = block[3]

    return "\n".join(body_lines), consumed

# Node interface (Chain of Responsibility)
class _ExtractionNode(ABC):
    """Nó abstrato da cadeia de extração."""

    @abstractmethod
    def extract(self, file_path: str, default_metadata: Dict) -> List[Document]:
        ...

# Node 1 — Local Parser (PyMuPDF + EasyOCR)
class LocalParserNode(_ExtractionNode):
    """Extração 100% local e gratuita via PyMuPDF com fallback OCR por página."""

    def extract(self, file_path: str, default_metadata: Dict) -> List[Document]:
        documents: List[Document] = []
        try:
            doc = fitz.open(file_path)
        except FileNotFoundError:
            logger.error(f"PDF não encontrado: {file_path}")
            raise
        except fitz.FileDataError as e:
            raise ValueError(f"Arquivo PDF inválido: {e}") from e

        try:
            total_pages = len(doc)
            ocr_pages = 0

            for page_num in range(total_pages):
                page = doc[page_num]
                base_meta = {**default_metadata, "page": page_num + 1, "source": file_path}
                all_blocks = page.get_text("blocks")

                table_docs, consumed = self._extract_tables(page, all_blocks, base_meta)

                text_parts = [b[4] for i, b in enumerate(all_blocks) if i not in consumed]
                text = "\n".join(text_parts)
                used_ocr = False

                if len(text.strip()) < _OCR_THRESHOLD:
                    logger.info(
                        f"Página {page_num + 1}/{total_pages}: texto escasso "
                        f"({len(text.strip())} chars) — ativando EasyOCR."
                    )
                    text = _ocr_page(page)
                    used_ocr = True
                    if text:
                        ocr_pages += 1
                    else:
                        logger.warning(f"Página {page_num + 1} sem texto mesmo após OCR.")
                        text = "[Página sem texto extraível]"

                text = _clean_text(text)
                if text:
                    meta = {**base_meta, "ocr_applied": used_ocr, "is_table": False}
                    documents.append(Document(page_content=text, metadata=meta))

                documents.extend(table_docs)

            if ocr_pages:
                logger.info(f"EasyOCR aplicado em {ocr_pages}/{total_pages} páginas.")
        finally:
            doc.close()

        return documents

    def _extract_tables(
        self,
        page: fitz.Page,
        all_blocks: list,
        base_meta: Dict,
    ) -> Tuple[List[Document], Set[int]]:
        table_docs: List[Document] = []
        all_consumed: Set[int] = set()

        try:
            tables = page.find_tables()
        except Exception as e:
            logger.warning(f"find_tables falhou na página {base_meta.get('page')}: {e}")
            return [], set()

        for i, table in enumerate(tables):
            header_bbox = fitz.Rect(table.bbox)
            header_md = _table_header_to_markdown(table)

            header_block_indices = {
                idx for idx, b in enumerate(all_blocks)
                if fitz.Rect(b[:4]).intersects(header_bbox)
            }

            body_md, body_block_indices = _collect_table_body(page, header_bbox, all_blocks)
            consumed = header_block_indices | body_block_indices
            all_consumed |= consumed

            full_md = (header_md + "\n" + body_md).strip() if body_md else header_md
            if not full_md:
                continue

            meta = {**base_meta, "is_table": True, "table_index": i, "ocr_applied": False}
            table_docs.append(Document(page_content=full_md, metadata=meta))

        return table_docs, all_consumed

# Node 2 — LLM Validator (Ollama / any BaseChatModel)
_SYSTEM_PROMPT = """\
Você é um validador de qualidade de extração de PDFs agronômicos para um sistema RAG.
Avalie texto corrido E integridade estrutural de tabelas numéricas.

Schema de resposta (JSON puro, sem markdown):
{
  "qualidade": "boa" | "parcial" | "falha",
  "texto_principal": "<primeiros 200 caracteres do texto extraído>",
  "tabelas": [],
  "motivo_falha": "<descrição se qualidade != boa, senão null>"
}

Critérios:
- "boa"    : texto legível E, se houver dados tabulares, os valores numéricos estão
             claramente associados aos seus cabeçalhos/colunas (ex: "Ca 2,5 cmolc dm⁻³").
- "parcial": texto legível MAS tabelas com valores numéricos embaralhados, colunas
             colapsadas numa linha só, ou unidades separadas dos valores
             (ex: "Baixo <0,02 <1 <0,4 Médio 0,02-1,5 1-2" sem cabeçalho associado).
- "falha"  : texto majoritariamente ilegível ou encoding corrompido.

REGRAS CRÍTICAS:
- Ausência de tabelas NÃO é "parcial" nem "falha" — documentos só-texto podem ser "boa".
- Tabelas com números soltos sem relação clara de coluna/linha devem ser "parcial".
- Responda SOMENTE o JSON, sem nenhum texto antes ou depois.
"""


def _build_validation_prompt(raw_text: str, previous_error: Optional[str] = None) -> str:
    header = "Texto bruto extraído do PDF:\n\n"
    if previous_error:
        header = (
            f"[RETRY] A tentativa anterior produziu JSON inválido: {previous_error}\n"
            "Corrija e retente.\n\n"
            + header
        )
    return header + raw_text[:6000]


class LLMValidatorNode(_ExtractionNode):
    """
    Valida a extração local usando um LLM menor (Ollama).

    Ao receber os Documents da extração local, concatena o texto bruto,
    pede ao LLM para mapear no schema Pydantic ExtractionResult e decide:
      - qualidade=="boa"/"parcial"  → retorna os Documents com metadado 'local'
      - qualidade=="falha"          → levanta LLMValidationFailed (ativa fallback)
    """

    def __init__(self, llm: BaseChatModel, local_node: LocalParserNode):
        self._llm = llm
        self._local_node = local_node

    def extract(self, file_path: str, default_metadata: Dict) -> List[Document]:
        local_docs = self._local_node.extract(file_path, default_metadata)
        raw_text = "\n\n".join(d.page_content for d in local_docs)

        result = self._validate_with_retry(raw_text)

        has_tables = any(d.metadata.get("is_table") for d in local_docs)

        if result.qualidade == ExtractionQuality.FALHA:
            logger.warning(
                f"[CUSTO: FALLBACK] Qualidade='falha' "
                f"(motivo: {result.motivo_falha}). Ativando LlamaParse."
            )
            raise LLMValidationFailed(result.motivo_falha or "qualidade==falha")

        if result.qualidade == ExtractionQuality.PARCIAL and has_tables:
            logger.warning(
                f"[CUSTO: FALLBACK] Qualidade='parcial' com tabelas detectadas "
                f"(motivo: {result.motivo_falha}). Ativando LlamaParse."
            )
            raise LLMValidationFailed(result.motivo_falha or "qualidade==parcial com tabelas")

        logger.info(f"[CUSTO: ZERO] Extração local validada com qualidade='{result.qualidade}'.")

        for doc in local_docs:
            doc.metadata["extraction_node"] = "pymupdf"
            doc.metadata["extraction_quality"] = result.qualidade.value
        return local_docs

    def _validate_with_retry(self, raw_text: str) -> ExtractionResult:
        last_error: Optional[str] = None

        for attempt in range(1, MAX_RETRIES + 1):
            prompt = _build_validation_prompt(raw_text, previous_error=last_error)
            messages = [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=prompt)]

            try:
                response = self._llm.invoke(messages)
                json_text = response.content.strip()
                if json_text.startswith("```"):
                    json_text = re.sub(r"^```[a-z]*\n?", "", json_text)
                    json_text = re.sub(r"\n?```$", "", json_text)

                result = ExtractionResult.model_validate_json(json_text)
                logger.debug(f"LLM Validator: tentativa {attempt} → qualidade='{result.qualidade}'")
                return result

            except (ValidationError, json.JSONDecodeError, ValueError) as e:
                last_error = str(e)
                logger.warning(
                    f"LLM Validator: tentativa {attempt}/{MAX_RETRIES} falhou "
                    f"({type(e).__name__}: {last_error[:120]}). "
                    + ("Retentando..." if attempt < MAX_RETRIES else "Retries esgotados.")
                )
            except Exception as e:
                logger.error(
                    f"LLM Validator: Ollama indisponível (tentativa {attempt}): {e}. "
                    "Retornando extração local sem validação."
                )
                raise LLMUnavailable(str(e)) from e

        logger.warning("LLM Validator: retries de parsing esgotados → qualidade=falha.")
        return ExtractionResult(
            qualidade=ExtractionQuality.FALHA,
            motivo_falha=f"Retries esgotados. Último erro: {last_error}",
        )


class LLMValidationFailed(Exception):
    """Sinaliza que o validador LLM julgou a extração local irrecuperável (qualidade=falha)."""


class LLMUnavailable(Exception):
    """Sinaliza falha de infraestrutura no Ollama (rede, timeout) — não aciona fallback premium."""

# Node 3 — LlamaParse Fallback (Lazy Loading)
class LlamaParseNode(_ExtractionNode):
    """
    Fallback premium via LlamaParse.
    O cliente é instanciado apenas no primeiro uso (Lazy Loading) para evitar
    consumo de memória e cold start quando não for necessário.
    """

    def __init__(self, api_key: str, result_type: str = "markdown"):
        self._api_key = api_key
        self._result_type = result_type
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from llama_parse import LlamaParse
            except ImportError as e:
                raise ImportError(
                    "llama-parse não instalado. Execute: pip install llama-parse"
                ) from e

            self._client = LlamaParse(
                api_key=self._api_key,
                result_type=self._result_type,
                language="pt",
                verbose=False,
            )
            logger.info("LlamaParseNode: cliente LlamaParse instanciado (lazy load).")
        return self._client

    def extract(self, file_path: str, default_metadata: Dict) -> List[Document]:
        logger.info(
            f"[CUSTO: LLAMAPARSE] Acionando fallback premium para '{file_path}'."
        )
        client = self._get_client()

        try:
            raw_docs = client.load_data(file_path)
        except Exception as e:
            logger.error(f"LlamaParse falhou: {e}")
            raise

        documents: List[Document] = []
        for i, raw in enumerate(raw_docs):
            text = getattr(raw, "text", "") or ""
            text = _clean_text(text)
            if not text:
                continue

            meta = {
                **default_metadata,
                "source": file_path,
                "page": i + 1,
                "is_table": False,
                "ocr_applied": False,
                "extraction_node": "llamaparse",
                "extraction_quality": "fallback",
            }
            documents.append(Document(page_content=text, metadata=meta))

        logger.info(
            f"[CUSTO: LLAMAPARSE] {len(documents)} documentos extraídos via LlamaParse."
        )
        return documents

# Orquestrador principal — PDFProcessor
def _build_ollama_llm() -> BaseChatModel:
    """Constrói o LLM local via Ollama."""
    from langchain_ollama import ChatOllama
    from config.settings import get_settings
    s = get_settings()
    return ChatOllama(model=s.LLM_MODEL, base_url=s.OLLAMA_BASE_URL, temperature=0)


class PDFProcessor:
    """
    Orquestrador da cadeia Local → Validator → LlamaParse.

    Parâmetros:
        file_path         : caminho do arquivo PDF.
        default_metadata  : metadados base propagados para todos os Documents.
        llm               : instância BaseChatModel para o validador (injetável;
                            padrão = Ollama configurado em Settings).
        llamaparse_key    : chave de API LlamaParse (injetável; padrão = env
                            LLAMAPARSE_API_KEY). Se None, o fallback lança ImportError.
    """

    def __init__(
        self,
        file_path: str,
        default_metadata: Optional[Dict] = None,
        llm: Optional[BaseChatModel] = None,
        llamaparse_key: Optional[str] = None,
    ):
        self.file_path = file_path
        self.default_metadata = default_metadata or {}
        self._llm_override = llm
        self._llamaparse_key_override = llamaparse_key
        self._validator: Optional[LLMValidatorNode] = None
        self._fallback: Optional[LlamaParseNode] = None

    @staticmethod
    def _resolve_llamaparse_key() -> Optional[str]:
        from config.settings import get_settings
        return get_settings().LLAMAPARSE_API_KEY

    def _ensure_nodes(self) -> None:
        """Constrói os nós na primeira chamada (lazy) para evitar ImportError no __init__."""
        if self._validator is not None:
            return
        local_node = LocalParserNode()
        _llm = self._llm_override or _build_ollama_llm()
        self._validator = LLMValidatorNode(llm=_llm, local_node=local_node)
        _key = self._llamaparse_key_override or self._resolve_llamaparse_key()
        self._fallback = LlamaParseNode(api_key=_key) if _key else None

    def extract_documents(self) -> List[Document]:
        """
        Executa a cadeia Local → Validator → LlamaParse e retorna Documents
        prontos para chunking e indexação no Qdrant.
        """
        self._ensure_nodes()
        try:
            return self._validator.extract(self.file_path, self.default_metadata)

        except LLMUnavailable:
            logger.warning(
                "[CUSTO: ZERO] Ollama indisponível — retornando extração local sem validação. "
                "Suba o Ollama para habilitar o validador."
            )
            local_docs = LocalParserNode().extract(self.file_path, self.default_metadata)
            for doc in local_docs:
                doc.metadata["extraction_node"] = "pymupdf"
                doc.metadata["extraction_quality"] = "unvalidated"
            return local_docs

        except LLMValidationFailed:
            if self._fallback is None:
                logger.error(
                    "[CUSTO: ZERO] Fallback LlamaParse não configurado (LLAMAPARSE_API_KEY ausente). "
                    "Retornando extração local sem validação."
                )
                local_docs = LocalParserNode().extract(self.file_path, self.default_metadata)
                for doc in local_docs:
                    doc.metadata["extraction_node"] = "pymupdf"
                    doc.metadata["extraction_quality"] = "unvalidated"
                return local_docs

            return self._fallback.extract(self.file_path, self.default_metadata)
