import os
import sys
import asyncio
from celery import Celery

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "agronomy_assistant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["workers.ingestion_worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True
)
