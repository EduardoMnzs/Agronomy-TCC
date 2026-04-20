import os
import time
import logging
import asyncio

if __import__("sys").platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger = logging.getLogger(__name__)

TEMP_FILE_TTL_SECONDS = int(os.environ.get("TEMP_FILE_TTL_SECONDS", 86400))  # 24h padrão


def _cleanup_expired_temp_files(temp_dir: str) -> None:
    """Remove arquivos temporários mais antigos que TEMP_FILE_TTL_SECONDS para evitar leak de disco."""
    if not os.path.isdir(temp_dir):
        return
    now = time.time()
    for fname in os.listdir(temp_dir):
        fpath = os.path.join(temp_dir, fname)
        try:
            if os.path.isfile(fpath) and (now - os.path.getctime(fpath)) > TEMP_FILE_TTL_SECONDS:
                os.remove(fpath)
                logger.info(f"Arquivo temporário expirado removido: {fpath}")
        except OSError as e:
            logger.warning(f"Não foi possível remover arquivo temporário '{fpath}': {e}")

from workers.celery_app import celery_app
from core.ingestion.pdf_processor import PDFProcessor
from core.ingestion.chunker import split_documents
from core.ingestion.metadata_enricher import enrich_chunks
from infrastructure.vectordb.qdrant_adapter import QdrantAdapter
from core.ingestion.parsers.csv_parser import CSVParser
from core.agents.metadata_extractor import MetadataExtractorAgent
from infrastructure.database.models import CatalogoFontes
from infrastructure.database.sync_session import get_sync_session

@celery_app.task(bind=True, name="inspect_document")
def inspect_document_task(self, file_path: str):
    """
    Task de estágio da esteira Human-in-The-Loop.
    Disparada quando o usuário faz upload sem declarar ID_fonte.
    Acorda o LLM, extrai o contexto, e salva no PostgreSQL como PENDENTE.
    """
    _cleanup_expired_temp_files(os.path.dirname(file_path))
    self.update_state(state="PROGRESS", meta={"status": "Iniciando inspeção profunda da IA..."})
    
    agent = MetadataExtractorAgent()
    metadata = asyncio.run(agent.extract_metadata(file_path))
    
    self.update_state(state="PROGRESS", meta={"status": "Gravando predição no Banco de Dados..."})

    with get_sync_session() as db:
        novo_catalogo = CatalogoFontes(**metadata)
        db.add(novo_catalogo)
        db.flush()
        db.refresh(novo_catalogo)

        catalogo_id = novo_catalogo.id
        catalogo_titulo = novo_catalogo.titulo
        catalogo_categoria = novo_catalogo.categoria_agronomica
    
    return {
        "status": "sucesso",
        "action": "Esperando aprovação humana",
        "id_gerado": catalogo_id,
        "titulo_sugerido": catalogo_titulo,
        "categoria_sugerida": catalogo_categoria
    }

@celery_app.task(bind=True, name="process_document")
def process_document_task(self, file_path: str, user_metadata: dict = None):
    """
    Worker híbrido: valida payload, roteia por extensão (PDF → Qdrant, CSV → Postgres)
    e garante limpeza do arquivo temporário independente do resultado.
    """
    _cleanup_expired_temp_files(os.path.dirname(file_path))
    metadata = user_metadata or {}

    if not metadata.get("id_fonte"):
        raise ValueError("'id_fonte' é obrigatório para rastreabilidade.")

    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        if file_ext == ".csv":
            self.update_state(state="PROGRESS", meta={"status": "Roteado para CSVParser (PostgreSQL)..."})
            return CSVParser(file_path, metadata).process()

        if file_ext == ".pdf":
            self.update_state(state="PROGRESS", meta={"status": "Extraindo fluxo textual do PDF..."})
            documents = PDFProcessor(file_path=file_path, default_metadata=metadata).extract_documents()

            if not documents:
                raise RuntimeError("Nenhum conteúdo extraível encontrado no PDF.")

            self.update_state(state="PROGRESS", meta={"status": "Separando sentenças em vetores RAG..."})
            chunks = split_documents(documents)

            self.update_state(state="PROGRESS", meta={"status": "Enriquecendo metadados semânticos dos chunks..."})
            chunks = enrich_chunks(chunks)

            self.update_state(state="PROGRESS", meta={"status": f"Persistindo {len(chunks)} chunks no Qdrant..."})
            QdrantAdapter().add_documents(chunks)

            return {
                "status": "sucesso",
                "chunks_persistidos": len(chunks),
                "paginas_processadas": len(documents),
            }

        raise ValueError(f"Extensão não suportada: '{file_ext}'. Use PDF ou CSV.")

    except ValueError:
        raise

    except Exception as exc:
        raise self.retry(exc=exc, max_retries=1, countdown=10)

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
