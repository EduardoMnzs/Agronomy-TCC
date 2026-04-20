from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any
from infrastructure.database.models import CatalogoFontes
from api.v1.schemas.catalog import CatalogoCreate, CatalogoUpdate

_UPDATABLE_FIELDS = {
    "titulo",
    "orgao_emissor",
    "tipo_documento",
    "categoria_agronomica",
    "data_publicacao",
    "url_ou_caminho_original",
    "status_processamento",
    "caminho_temporario",
}

async def create_catalogo(db: AsyncSession, catalogo_in: CatalogoCreate) -> CatalogoFontes:
    """Registra uma nova fonte agronômica, gerando um ID fixo para rastreabilidade."""
    novo_catalogo = CatalogoFontes(**catalogo_in.model_dump())
    db.add(novo_catalogo)
    await db.commit()
    await db.refresh(novo_catalogo)
    return novo_catalogo

async def get_catalogo_by_id(db: AsyncSession, catalogo_id: int) -> Optional[CatalogoFontes]:
    """Busca um registro exato do catálogo pelo ID mestre."""
    query = select(CatalogoFontes).where(CatalogoFontes.id == catalogo_id)
    result = await db.execute(query)
    return result.scalars().first()

async def update_catalogo(db: AsyncSession, catalogo_id: int, updates: Dict[str, Any]) -> Optional[CatalogoFontes]:
    """Atualiza metadados ou status da fonte."""
    campos_invalidos = set(updates.keys()) - _UPDATABLE_FIELDS
    if campos_invalidos:
        raise ValueError(f"Campos não permitidos para atualização: {campos_invalidos}")

    catalogo = await get_catalogo_by_id(db, catalogo_id)
    if catalogo:
        for key, value in updates.items():
            setattr(catalogo, key, value)
        await db.commit()
        await db.refresh(catalogo)
    return catalogo

async def list_catalogos(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[CatalogoFontes]:
    """Lista as fontes com paginação para visualização administrativa."""
    query = select(CatalogoFontes).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def delete_catalogo(db: AsyncSession, catalogo_id: int) -> bool:
    """Exclui a raiz primária de dados. Todo chunk atrelado a ele ficará sem owner."""
    query = select(CatalogoFontes).where(CatalogoFontes.id == catalogo_id)
    result = await db.execute(query)
    obj = result.scalars().first()
    
    if obj:
        await db.delete(obj)
        await db.commit()
        return True
    return False
