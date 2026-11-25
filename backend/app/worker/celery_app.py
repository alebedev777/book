from celery import Celery
from celery.schedules import crontab

from app.config import get_settings
from app.observability import configure_langfuse

settings = get_settings()
configure_langfuse()

celery_app = Celery(
    "book",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-expired-photos": {
            "task": "app.worker.tasks.cleanup_expired_photos",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)