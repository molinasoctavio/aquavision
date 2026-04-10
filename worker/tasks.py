"""Celery tasks — bridge between HTTP triggers and agent pipeline."""
import asyncio
import json
import os

from worker.celery_app import celery_app
from app.config import get_settings
import structlog

settings = get_settings()
logger = structlog.get_logger()


def _run_async(coro):
    """Run async coroutine in sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="worker.tasks.process_video_pipeline", max_retries=3)
def process_video_pipeline(self, video_id: str, storage_path: str, match_id: str = None):
    """Full video processing pipeline: ingest → transcode → stabilize → HLS."""
    try:
        logger.info("Starting video pipeline", video_id=video_id)
        from agents.video_ingestion_agent import VideoIngestionAgent
        agent = VideoIngestionAgent()
        result = _run_async(agent.process({
            "video_id": video_id,
            "source_type": "upload",
            "storage_path": storage_path,
            "match_id": match_id,
            "task_type": "ingest",
        }))
        return result
    except Exception as exc:
        logger.error("Pipeline failed", video_id=video_id, error=str(exc))
        self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, name="worker.tasks.run_ai_detection", max_retries=2)
def run_ai_detection(self, video_id: str, processed_path: str, match_id: str = None):
    """Run AI detection on processed video."""
    try:
        from agents.waterpolo_detection_agent import WaterpoloDetectionAgent
        agent = WaterpoloDetectionAgent()
        result = _run_async(agent.process({
            "video_id": video_id,
            "processed_path": processed_path,
            "match_id": match_id,
            "task_type": "detect",
        }))
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, name="worker.tasks.generate_analytics", max_retries=2)
def generate_analytics(self, video_id: str, match_id: str, results_path: str):
    """Compute analytics from detection results."""
    try:
        from agents.analytics_engine_agent import AnalyticsEngineAgent
        agent = AnalyticsEngineAgent()
        result = _run_async(agent.process({
            "video_id": video_id,
            "match_id": match_id,
            "results_path": results_path,
            "task_type": "compute_analytics",
        }))
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, name="worker.tasks.export_clip", max_retries=3)
def export_clip(self, clip_id: str, video_id: str, start_ms: int, end_ms: int, quality: str = "1080p"):
    """Export a clip to MP4."""
    try:
        from agents.video_processing_agent import VideoProcessingAgent
        agent = VideoProcessingAgent()
        result = _run_async(agent.process({
            "task_type": "clip_export",
            "clip_id": clip_id,
            "video_id": video_id,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "quality": quality,
        }))
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=15)


@celery_app.task(name="worker.tasks.generate_post_match_report")
def generate_post_match_report(match_id: str, user_id: str):
    """Generate AI post-match analysis report."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models.analytics import MatchAnalytics
    from app.services.coach_assist import CoachAssistService
    from uuid import UUID

    engine = create_engine(settings.DATABASE_SYNC_URL)
    with Session(engine) as session:
        async def _gen():
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                service = CoachAssistService(db)
                summary = await service.generate_post_match_summary(match_id)
                ma = session.execute(
                    session.query(MatchAnalytics).filter_by(match_id=UUID(match_id))
                ).scalar_one_or_none()
                if ma:
                    ma.ai_summary = summary
                    session.commit()
                return summary

        return _run_async(_gen())


@celery_app.task(name="worker.tasks.export_social")
def export_social_clip(clip_id: str, video_id: str, start_ms: int, end_ms: int, platform: str):
    """Export clip in social media format."""
    from agents.sharing_export_agent import SharingExportAgent
    agent = SharingExportAgent()
    return _run_async(agent.process({
        "task_type": "export_social",
        "clip_id": clip_id,
        "video_id": video_id,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "platform": platform,
    }))
