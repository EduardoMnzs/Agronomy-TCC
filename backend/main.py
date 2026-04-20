import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from api.v1.routes.ingestion import router as ingestion_router
from api.v1.routes.catalog import router as catalog_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Agronomy Assistant API", version="1.0.0")

app.include_router(ingestion_router, prefix="/api/v1/ingestion", tags=["Ingestion Poliglota"])
app.include_router(catalog_router, prefix="/api/v1/catalog", tags=["Rastreabilidade (Catálogo Base)"])


@app.get("/")
def read_root():
    return {"message": "Bem vindo a API do Agronomy Assistant"}


@app.get("/health", tags=["Infra"])
async def health_check():
    """
    Verifica a conectividade real com Postgres, Redis e Qdrant.
    Retorna 200 somente quando todos os serviços estão acessíveis.
    """
    from infrastructure.database.sync_session import get_sync_session
    from sqlalchemy import text as sa_text
    from config.settings import get_settings
    import redis as redis_lib
    from qdrant_client import QdrantClient

    settings = get_settings()
    checks: dict = {}
    healthy = True

    # --- Postgres ---
    try:
        with get_sync_session() as db:
            db.execute(sa_text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        logger.error(f"Health check Postgres falhou: {e}")
        checks["postgres"] = "unavailable"
        healthy = False

    # --- Redis ---
    try:
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        logger.error(f"Health check Redis falhou: {e}")
        checks["redis"] = "unavailable"
        healthy = False

    # --- Qdrant ---
    try:
        import os
        from infrastructure.vectordb.qdrant_adapter import _QDRANT_LOCAL_PATH

        if settings.ENVIRONMENT == "development":
            client = QdrantClient(path=_QDRANT_LOCAL_PATH)
        else:
            client = QdrantClient(
                url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
                api_key=settings.QDRANT_API_KEY,
                timeout=2,
            )
        client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as e:
        logger.error(f"Health check Qdrant falhou: {e}")
        checks["qdrant"] = "unavailable"
        healthy = False

    status_code = 200 if healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if healthy else "degraded", "checks": checks},
    )
