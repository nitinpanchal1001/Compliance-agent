from celery import Celery
from core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "compliance_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        # task modules registered here as phases are built
        # "workers.tasks.ingestion",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)
