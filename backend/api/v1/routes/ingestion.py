import os
import shutil
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from workers.ingestion_worker import process_document_task, inspect_document_task
from celery.result import AsyncResult
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()

TEMP_DIR = Path(os.environ.get("TEMP_UPLOADS_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "temp_uploads")))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE_MB = 100

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    id_fonte: Optional[int] = Form(None, description="Se deixado em branco, a IA atuará criando a base Curatorial PENDENTE")
):
    """Recebe o arquivo e injeta na maquina de fila imediatamente."""
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in [".pdf", ".csv"]:
        raise HTTPException(status_code=400, detail="Formato invalido. Utilize .pdf ou .csv")

    safe_filename = f"{uuid.uuid4().hex}{file_ext}"
    save_path = TEMP_DIR / safe_filename

    if not str(save_path.resolve()).startswith(str(TEMP_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Caminho inválido.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Arquivo excede o limite de {MAX_FILE_SIZE_MB}MB.")

    with open(save_path, "wb") as buffer:
        buffer.write(content)
        
    save_path_str = str(save_path)

    if not id_fonte or id_fonte <= 0:
        task = inspect_document_task.delay(save_path_str)
    else:
        task = process_document_task.delay(
            save_path_str,
            user_metadata={"filename": file.filename, "id_fonte": id_fonte}
        )
    
    return {
        "message": "Solicitacao de ingestao aceita!", 
        "task_id": task.id
    }

@router.get("/status/{task_id}")
async def get_ingestion_status(task_id: str):
    """Consulta rápida com Redis para ver o andamento live."""
    task = AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {"state": task.state, "status": "Na fila do worker..."}
    elif task.state == 'PROGRESS':
        response = {"state": task.state, "status": task.info.get("status", "")}
    elif task.state == 'SUCCESS':
        response = {"state": task.state, "result": task.result}
    else: 
        response = {"state": task.state, "status": str(task.info)}
        
    return response
