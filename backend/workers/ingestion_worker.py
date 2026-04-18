import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.celery_app import celery_app
from core.ingestion.pdf_processor import PDFProcessor
from core.ingestion.chunker import split_documents
from infrastructure.vectordb.qdrant_adapter import QdrantAdapter

@celery_app.task(bind=True, name="process_pdf")
def process_pdf_task(self, file_path: str, user_metadata: dict = None):
    """
    Worker job operando fora do loop HTTP (Event Loop do FastAPI), 
    garantido robustez com vetores massivos.
    """
    metadata = user_metadata or {}
    
    try:
        # Passo 1
        self.update_state(state="PROGRESS", meta={"status": "Extraindo fluxo textual do PDF..."})
        processor = PDFProcessor(file_path=file_path, default_metadata=metadata)
        documents = processor.extract_documents()
        
        if not documents:
            raise Exception("Parsing falhou de extrair caracters indexáveis.")
            
        # Passo 2
        self.update_state(state="PROGRESS", meta={"status": "Separando sentenças em vetores RAG..."})
        chunks = split_documents(documents)
        
        # Passo 3
        self.update_state(state="PROGRESS", meta={"status": f"Gerando embeddings e persistindo no DB ({len(chunks)} chunks)..."})
        qdrant = QdrantAdapter() 
        qdrant.add_documents(chunks)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {
            "status": "sucesso", 
            "chunks_persistidos": len(chunks),
            "paginas_corridas": len(documents)
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, max_retries=1, countdown=10)
