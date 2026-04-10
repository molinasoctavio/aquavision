"""
DBWriterAgent — Persists analysis results to PostgreSQL.
Bridges the async worker world and the database layer.
"""
import json
import secrets
from uuid import UUID

import sqlalchemy
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from agents.base_agent import BaseAgent
from app.config import get_settings
from app.services.storage import StorageService
from app.models.video import Video, VideoStatus
from app.models.match import Match, MatchEvent, EventType, MatchPeriod
from app.models.analytics import MatchAnalytics, PlayerMatchStats, ShotRecord
from app.models.clip import Clip

settings = get_settings()


class DBWriterAgent(BaseAgent):
    """Writes processed analysis data to the database."""

    def __init__(self):
        super().__init__("db_writer")
        self.storage = StorageService()
        self.engine = create_engine(settings.DATABASE_SYNC_URL)

    async def process(self, task: dict) -> dict:
        task_type = task.get("task_type")

        if task_type == "write_analytics":
            return self._write_analytics(task)
        elif task_type == "write_clips":
            return self._write_clips(task)
        elif task_type == "update_video_status":
            return self._update_video_status(task)
        return {}

    def _write_analytics(self, task: dict) -> dict:
        video_id = task["video_id"]
        match_id = task.get("match_id")
        analytics_path = task["analytics_path"]

        raw = self.storage.download_file(analytics_path, bucket=settings.S3_BUCKET_PROCESSED)
        analytics_data = json.loads(raw)

        with Session(self.engine) as session:
            # Update video status to READY
            video = session.get(Video, UUID(video_id))
            if video:
                video.status = VideoStatus.READY
                video.processing_progress = 1.0
                if task.get("hls_path"):
                    video.hls_path = task["hls_path"]
                if task.get("thumbnail_path"):
                    video.thumbnail_path = task["thumbnail_path"]
                video.is_stabilized = True

            if not match_id:
                session.commit()
                return {"status": "video_updated"}

            mid = UUID(match_id)

            # Write MatchAnalytics
            existing = session.execute(
                select(MatchAnalytics).where(MatchAnalytics.match_id == mid)
            ).scalar_one_or_none()

            poss = analytics_data.get("possession", {})
            quarter_stats = analytics_data.get("quarter_stats", {})
            event_counts = analytics_data.get("event_counts", {})

            if existing:
                ma = existing
            else:
                ma = MatchAnalytics(match_id=mid)
                session.add(ma)

            ma.home_possession_pct = poss.get("home_pct", 50.0)
            ma.away_possession_pct = poss.get("away_pct", 50.0)
            ma.home_shots = event_counts.get("shot_on_target", 0) + event_counts.get("goal", 0)
            ma.away_shots = event_counts.get("shot_on_target", 0)
            ma.home_power_play_attempts = analytics_data.get("power_play", {}).get("total_opportunities", 0)
            ma.home_power_play_goals = analytics_data.get("power_play", {}).get("goals_scored", 0)
            ma.momentum_timeline = analytics_data.get("momentum_timeline")
            ma.quarter_stats = quarter_stats

            # Write match events from detections
            events = analytics_data.get("event_counts", {})
            # (events were written during detection phase)

            session.commit()
            self.publish_status(video_id, "db_written", 1.0)

        return {"status": "analytics_written"}

    def _write_clips(self, task: dict) -> dict:
        video_id = task["video_id"]
        match_id = task.get("match_id")
        manifest_path = task["clips_manifest_path"]

        raw = self.storage.download_file(manifest_path, bucket=settings.S3_BUCKET_PROCESSED)
        clips_data = json.loads(raw)

        if not match_id:
            return {"status": "no_match_id"}

        mid = UUID(match_id)

        with Session(self.engine) as session:
            vid_result = session.execute(
                select(Video).where(Video.id == UUID(video_id))
            ).scalar_one_or_none()

            if not vid_result:
                return {"status": "video_not_found"}

            clips_written = 0
            for clip_data in clips_data:
                clip = Clip(
                    match_id=mid,
                    video_id=UUID(video_id),
                    created_by=vid_result.uploaded_by,
                    title=clip_data["title"],
                    start_ms=clip_data["start_ms"],
                    end_ms=clip_data["end_ms"],
                    duration_ms=clip_data["duration_ms"],
                    is_auto_generated=True,
                    ability_labels=clip_data.get("ability_labels", []),
                    share_token=secrets.token_urlsafe(32),
                )
                session.add(clip)
                clips_written += 1

            session.commit()

        return {"status": "clips_written", "count": clips_written}

    def _update_video_status(self, task: dict) -> dict:
        with Session(self.engine) as session:
            video = session.get(Video, UUID(task["video_id"]))
            if video:
                video.status = VideoStatus(task["status"])
                video.processing_progress = task.get("progress", 0.0)
                if task.get("error"):
                    video.processing_error = task["error"]
                session.commit()
        return {"status": "updated"}
