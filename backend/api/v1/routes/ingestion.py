import os
import shutil
from fastapi import APIRouter, File, UploadFile, HTTPException
from workers.ingestion_worker import process_pdf_task
from celery.result import AsyncResult

router = APIRouter()

TEMP_DIR = os.path.join(os.getcwd(), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Recebe o arquivo e injeta na maquina de fila imediatamente."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Formato invalido, envie padrao .pdf")
        
    save_path = os.path.join(TEMP_DIR, file.filename)
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # O comando mágico ".delay" aciona o Garçom Celery.
    task = process_pdf_task.delay(save_path, user_metadata={"filename": file.filename})
    
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
