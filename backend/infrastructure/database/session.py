from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from config.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.POSTGRES_URL, 
    echo=settings.DEBUG,
    future=True,
    poolclass=NullPool
)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Injeção de dependência do FastAPI para retornar sessões de banco assíncronas.
    O commit é responsabilidade de cada operação no repository.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
