"""Celery application for background task processing."""
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "aquavision",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["worker.tasks"],
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
    task_routes={
        "worker.tasks.process_video_pipeline": {"queue": "video"},
        "worker.tasks.run_ai_detection":       {"queue": "ai"},
        "worker.tasks.export_clip":            {"queue": "export"},
        "worker.tasks.generate_analytics":     {"queue": "analytics"},
    },
    task_soft_time_limit=7200,
    task_time_limit=10800,
)
