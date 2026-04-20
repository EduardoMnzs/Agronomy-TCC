from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import get_settings

_settings = get_settings()

_SYNC_URL = (
    f"postgresql+psycopg2://{_settings.POSTGRES_USER}:{_settings.POSTGRES_PASSWORD}"
    f"@{_settings.POSTGRES_HOST}:{_settings.POSTGRES_PORT}/{_settings.POSTGRES_DB}"
)

_sync_engine = create_engine(
    _SYNC_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

_SyncSessionFactory = sessionmaker(bind=_sync_engine, autocommit=False, autoflush=False)


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Context manager para sessões síncronas."""
    session = _SyncSessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
