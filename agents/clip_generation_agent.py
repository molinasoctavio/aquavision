"""
ClipGenerationAgent — Automatically creates clips from detected events.
Also handles manual clip exports with follow-cam and keyframe rendering.
"""
import json
from collections import defaultdict

from agents.base_agent import BaseAgent
from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()

# Context padding for each event type (ms before/after)
CLIP_PADDING = {
    "goal":               {"pre": 8000,  "post": 5000},
    "shot_on_target":     {"pre": 5000,  "post": 4000},
    "shot_blocked":       {"pre": 5000,  "post": 3000},
    "exclusion":          {"pre": 4000,  "post": 6000},
    "penalty_5m":         {"pre": 5000,  "post": 5000},
    "power_play_start":   {"pre": 3000,  "post": 20000},
    "counterattack":      {"pre": 2000,  "post": 8000},
    "period_start":       {"pre": 0,     "post": 10000},
    "save":               {"pre": 5000,  "post": 3000},
    "steal":              {"pre": 3000,  "post": 4000},
    "default":            {"pre": 4000,  "post": 3000},
}


class ClipGenerationAgent(BaseAgent):
    def __init__(self):
        super().__init__("clip_generation")
        self.storage = StorageService()

    async def process(self, task: dict) -> dict:
        task_type = task.get("task_type", "auto_clips")
        if task_type == "auto_clips":
            return await self._auto_generate_clips(task)
        elif task_type == "export_clip":
            return await self._export_single_clip(task)
        return {}

    async def _auto_generate_clips(self, task: dict) -> dict:
        video_id = task["video_id"]
        match_id = task.get("match_id")
        events = task.get("events", [])

        self.publish_status(video_id, "generating_clips", 0.0)

        # Filter to significant events only
        significant_types = {
            "goal", "shot_on_target", "shot_blocked", "exclusion",
            "penalty_5m", "power_play_start", "counterattack", "save", "steal",
        }

        clips_metadata = []
        for i, event in enumerate(events):
            if event["event_type"] not in significant_types:
                continue

            padding = CLIP_PADDING.get(event["event_type"], CLIP_PADDING["default"])
            start_ms = max(0, event["timestamp_ms"] - padding["pre"])
            end_ms = event["timestamp_ms"] + padding["post"]

            clip_meta = {
                "video_id": video_id,
                "match_id": match_id,
                "event_type": event["event_type"],
                "period": event["period"],
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": end_ms - start_ms,
                "event_timestamp_ms": event["timestamp_ms"],
                "position_x": event.get("position_x"),
                "position_y": event.get("position_y"),
                "details": event.get("details", {}),
                "confidence": event.get("confidence", 0.0),
                "is_auto_generated": True,
                "title": self._generate_clip_title(event),
                "ability_labels": self._suggest_ability_labels(event),
            }
            clips_metadata.append(clip_meta)

        # Save clips manifest
        manifest_path = f"analysis/{video_id}/clips_manifest.json"
        self.storage.upload_bytes(
            json.dumps(clips_metadata).encode(),
            manifest_path,
            bucket=settings.S3_BUCKET_PROCESSED,
            content_type="application/json",
        )

        self.publish_status(video_id, "clips_ready", 1.0)

        # Forward to DB writer to persist everything
        self.enqueue_next("db_writer", {
            "task_type": "write_clips",
            "video_id": video_id,
            "match_id": match_id,
            "clips_manifest_path": manifest_path,
        })

        return {"status": "generated", "clips_count": len(clips_metadata)}

    async def _export_single_clip(self, task: dict) -> dict:
        """Export a single clip (render to MP4)."""
        self.enqueue_next("video_processing", {
            "task_type": "clip_export",
            "video_id": task["video_id"],
            "clip_id": task["clip_id"],
            "start_ms": task["start_ms"],
            "end_ms": task["end_ms"],
            "quality": task.get("quality", "1080p"),
        })
        return {"status": "queued_for_export"}

    def _generate_clip_title(self, event: dict) -> str:
        titles = {
            "goal": "⚽ Goal",
            "shot_on_target": "Shot on Target",
            "shot_blocked": "Shot Blocked",
            "exclusion": "Exclusion (6v5)",
            "penalty_5m": "5-Meter Penalty",
            "power_play_start": "Power Play Start",
            "counterattack": "Counterattack",
            "save": "Save",
            "steal": "Steal",
        }
        base = titles.get(event["event_type"], event["event_type"].replace("_", " ").title())
        period = event.get("period", "")
        return f"{base} — {period}" if period else base

    def _suggest_ability_labels(self, event: dict) -> list[str]:
        label_map = {
            "goal": ["shooting", "finishing"],
            "shot_on_target": ["shooting"],
            "shot_blocked": ["defense", "blocking"],
            "exclusion": ["defense"],
            "power_play_start": ["tactical"],
            "counterattack": ["speed", "counterattack"],
            "save": ["goalkeeping", "defense"],
            "steal": ["defense", "interception"],
        }
        return label_map.get(event["event_type"], [])
