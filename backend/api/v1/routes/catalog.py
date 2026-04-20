import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from infrastructure.database.session import get_db
from infrastructure.database import repository
from api.v1.schemas.catalog import CatalogoCreate, CatalogoResponse, CatalogoUpdate
from workers.ingestion_worker import process_document_task

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=CatalogoResponse, status_code=status.HTTP_201_CREATED)
async def registrar_fonte_agronomica(
    catalogo_in: CatalogoCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cadastra a Identidade raiz de uma fonte no Banco Relacional.
    Devolve um ID que servirá de "passaporte" no ato do upload de arquivos físicos.
    """
    try:
        resultado = await repository.create_catalogo(db, catalogo_in)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao registrar fonte agronômica: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")

@router.get("/", response_model=List[CatalogoResponse])
async def ver_todas_fontes(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """
    Lista paginada de todos os metadados (Órgão emissor, Autorias, etc).
    """
    catalogos = await repository.list_catalogos(db, skip=skip, limit=limit)
    return catalogos

@router.get("/{id_fonte}", response_model=CatalogoResponse)
async def ver_fonte_por_id(id_fonte: int, db: AsyncSession = Depends(get_db)):
    """Busca para checar as propriedades prévias de um upload já aprovado."""
    catalogo = await repository.get_catalogo_by_id(db, id_fonte)
    if not catalogo:
        raise HTTPException(status_code=404, detail="Fonte não mapeada no diretório Master.")
    return catalogo

@router.patch("/{id_fonte}/approve", response_model=CatalogoResponse)
async def aprovar_fonte_pendente(
    id_fonte: int, 
    correcoes: CatalogoUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Passo final do Human-in-The-Loop.
    O Curador envia as correções (se a IA tiver errado o Título/Órgão).
    O sistema salva, altera pra 'APROVADO' e despacha o arquivo físico pro VectorDB.
    """
    catalogo = await repository.get_catalogo_by_id(db, id_fonte)
    if not catalogo:
        raise HTTPException(status_code=404, detail="Catálogo Pendente não encontrado.")
    
    if catalogo.status_processamento == "APROVADO":
        raise HTTPException(status_code=400, detail="Essa fonte já foi aprovada e ingerida anteriormente.")
    
    updates = correcoes.model_dump(exclude_unset=True)
    updates["status_processamento"] = "APROVADO"
    
    catalogo_aprovado = await repository.update_catalogo(db, id_fonte, updates)
    
    if catalogo.caminho_temporario:
        if not os.path.exists(catalogo.caminho_temporario):
            logger.error(f"Arquivo temporário não encontrado para id_fonte={id_fonte}: {catalogo.caminho_temporario}")
            raise HTTPException(status_code=409, detail="Arquivo temporário não encontrado. O upload pode ter expirado.")
        try:
            process_document_task.delay(
                catalogo.caminho_temporario,
                user_metadata={"id_fonte": id_fonte}
            )
        except Exception as e:
            logger.error(f"Falha ao enfileirar task de ingestão para id_fonte={id_fonte}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro interno do servidor.")

    return catalogo_aprovado

@router.delete("/{id_fonte}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_fonte(id_fonte: int, db: AsyncSession = Depends(get_db)):
    """Remove a raiz da rastreabilidade."""
    sucesso = await repository.delete_catalogo(db, id_fonte)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Catálogo não encontrado ID inválido.")
    return None
