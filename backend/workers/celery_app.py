import os
import sys
from celery import Celery

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
