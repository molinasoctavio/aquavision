"""
SharingExportAgent — Handles clip/match sharing, social media exports, notifications.
"""
import json
import os
import subprocess
import tempfile
from app.config import get_settings
from app.services.storage import StorageService
from agents.base_agent import BaseAgent

settings = get_settings()

SOCIAL_PRESETS = {
    "instagram_story": {"w": 1080, "h": 1920, "max_s": 60, "fps": 30},
    "instagram_feed":  {"w": 1080, "h": 1080, "max_s": 60, "fps": 30},
    "tiktok":          {"w": 1080, "h": 1920, "max_s": 60, "fps": 30},
    "twitter":         {"w": 1280, "h": 720,  "max_s": 140, "fps": 30},
    "youtube_shorts":  {"w": 1080, "h": 1920, "max_s": 60, "fps": 30},
    "whatsapp":        {"w": 960,  "h": 540,  "max_s": 90, "fps": 25},
}


class SharingExportAgent(BaseAgent):
    def __init__(self):
        super().__init__("sharing_export")
        self.storage = StorageService()

    async def process(self, task: dict) -> dict:
        task_type = task.get("task_type")
        if task_type == "export_social":
            return await self._export_social(task)
        elif task_type == "generate_share_link":
            return await self._generate_share_link(task)
        elif task_type == "send_notification":
            return await self._send_notification(task)
        return {}

    async def _export_social(self, task: dict) -> dict:
        clip_id = task["clip_id"]
        video_id = task["video_id"]
        platform = task.get("platform", "instagram_feed")
        preset = SOCIAL_PRESETS.get(platform, SOCIAL_PRESETS["instagram_feed"])
        start_ms = task["start_ms"]
        end_ms = task["end_ms"]

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.mp4")
            output_path = os.path.join(tmpdir, f"{platform}.mp4")

            source_path = f"processed/{video_id}/video.mp4"
            self.storage.download_to_file(
                source_path, input_path,
                bucket=settings.S3_BUCKET_PROCESSED
            )

            start_s = start_ms / 1000
            duration_s = min((end_ms - start_ms) / 1000, preset["max_s"])
            w, h = preset["w"], preset["h"]

            # Letterbox/pillarbox to target aspect ratio
            vf = (
                f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"
            )
            cmd = [
                settings.FFMPEG_PATH,
                "-ss", str(start_s),
                "-i", input_path,
                "-t", str(duration_s),
                "-vf", vf,
                "-r", str(preset["fps"]),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                "-y",
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=300)

            export_path = f"exports/{clip_id}/{platform}.mp4"
            with open(output_path, "rb") as f:
                self.storage.upload_bytes(
                    f.read(), export_path,
                    bucket=settings.S3_BUCKET_CLIPS,
                    content_type="video/mp4",
                )

        return {"status": "exported", "path": export_path, "platform": platform}

    async def _generate_share_link(self, task: dict) -> dict:
        clip_id = task.get("clip_id")
        match_id = task.get("match_id")
        expires_hours = task.get("expires_hours", 168)  # 7 days default

        resource = clip_id or match_id
        if not resource:
            return {"status": "error", "message": "No resource specified"}

        path = f"clips/{clip_id}/clip.mp4" if clip_id else f"processed/{match_id}/video.mp4"
        bucket = settings.S3_BUCKET_CLIPS if clip_id else settings.S3_BUCKET_PROCESSED

        try:
            url = await self.storage.get_presigned_url(path, bucket=bucket, expires_hours=expires_hours)
            return {"status": "ok", "url": url}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _send_notification(self, task: dict) -> dict:
        """Send email/push notification (stub — integrate with actual service)."""
        notification_type = task.get("notification_type", "video_ready")
        user_id = task.get("user_id")
        payload = task.get("payload", {})

        self.logger.info(
            "Notification sent",
            type=notification_type,
            user_id=user_id,
            payload=payload,
        )
        return {"status": "sent", "type": notification_type}
