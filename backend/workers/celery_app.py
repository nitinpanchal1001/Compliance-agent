import ssl

from celery import Celery

from core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "compliance_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.tasks.ingestion",
        "workers.tasks.analysis",
        "workers.tasks.notifications",
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

if settings.celery_broker_url.startswith("rediss://"):
    _ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    celery_app.conf.update(
        broker_use_ssl=_ssl,
        redis_backend_use_ssl=_ssl,
    )
