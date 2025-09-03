from celery import Celery
from settings import REDIS_URL

celery_app = Celery(
    "video_service",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_default_queue="default",
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    result_expires=3600,
    timezone="UTC",
    enable_utc=True,
)