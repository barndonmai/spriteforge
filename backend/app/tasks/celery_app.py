from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "spriteforge",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.jobs"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

