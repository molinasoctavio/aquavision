"""
VideoIngestionAgent — Accepts video from any source and normalizes to unified pipeline.

Supported sources: file upload, URL (YouTube, direct), RTMP/RTSP streams,
IP cameras, mobile app, cloud drives (Google Drive, Dropbox).
"""
import os
import subprocess
import json
import tempfile
from pathlib import Path

from agents.base_agent import BaseAgent
from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()


class VideoIngestionAgent(BaseAgent):
    def __init__(self):
        super().__init__("video_ingestion")
        self.storage = StorageService()
        self.supported_formats = settings.SUPPORTED_VIDEO_FORMATS

    async def process(self, task: dict) -> dict:
        video_id = task["video_id"]
        source_type = task.get("source_type", "upload")
        self.publish_status(video_id, "ingesting", 0.0)

        if source_type == "upload":
            return await self._ingest_upload(task)
        elif source_type in ("url", "youtube"):
            return await self._ingest_url(task)
        elif source_type in ("rtmp", "rtsp"):
            return await self._ingest_stream(task)
        elif source_type == "ip_camera":
            return await self._ingest_ip_camera(task)
        else:
            return await self._ingest_upload(task)

    async def _ingest_upload(self, task: dict) -> dict:
        """Process an already-uploaded file."""
        video_id = task["video_id"]
        storage_path = task.get("storage_path")

        if not storage_path:
            raise ValueError("No storage_path provided for upload ingestion")

        # Probe the video file
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "input_video")
            self.storage.download_to_file(storage_path, local_path)
            metadata = self._probe_video(local_path)

        self.publish_status(video_id, "ingested", 1.0, details=metadata)

        # Forward to processing agent
        self.enqueue_next("video_processing", {
            "video_id": video_id,
            "storage_path": storage_path,
            "metadata": metadata,
            "task_type": "transcode",
        })

        return {"status": "ingested", "metadata": metadata}

    async def _ingest_url(self, task: dict) -> dict:
        """Download video from URL (supports YouTube via yt-dlp)."""
        video_id = task["video_id"]
        url = task["source_url"]
        self.publish_status(video_id, "downloading", 0.1)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, f"{video_id}.mp4")

            if "youtube.com" in url or "youtu.be" in url:
                # Use yt-dlp for YouTube
                cmd = [
                    "yt-dlp",
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                    "--merge-output-format", "mp4",
                    "-o", output_path,
                    url,
                ]
            else:
                # Direct download with ffmpeg
                cmd = [
                    settings.FFMPEG_PATH,
                    "-i", url,
                    "-c", "copy",
                    "-y",
                    output_path,
                ]

            self.logger.info("Downloading video", url=url, cmd=" ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            if result.returncode != 0:
                raise RuntimeError(f"Download failed: {result.stderr[:500]}")

            self.publish_status(video_id, "downloading", 0.7)

            # Probe metadata
            metadata = self._probe_video(output_path)

            # Upload to storage
            storage_path = f"raw/{video_id}/video.mp4"
            with open(output_path, "rb") as f:
                self.storage.upload_bytes(
                    f.read(), storage_path,
                    bucket=settings.S3_BUCKET_RAW,
                    content_type="video/mp4",
                )

        self.publish_status(video_id, "ingested", 1.0, details=metadata)

        self.enqueue_next("video_processing", {
            "video_id": video_id,
            "storage_path": storage_path,
            "metadata": metadata,
            "task_type": "transcode",
        })

        return {"status": "ingested", "metadata": metadata}

    async def _ingest_stream(self, task: dict) -> dict:
        """Record from RTMP/RTSP stream."""
        video_id = task["video_id"]
        stream_url = task["source_url"]
        duration = task.get("duration_seconds", 7200)  # default 2 hours

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, f"{video_id}.mp4")

            cmd = [
                settings.FFMPEG_PATH,
                "-i", stream_url,
                "-c", "copy",
                "-t", str(duration),
                "-y",
                output_path,
            ]

            self.publish_status(video_id, "recording", 0.1)
            subprocess.run(cmd, capture_output=True, timeout=duration + 60)

            metadata = self._probe_video(output_path)
            storage_path = f"raw/{video_id}/video.mp4"
            with open(output_path, "rb") as f:
                self.storage.upload_bytes(
                    f.read(), storage_path,
                    bucket=settings.S3_BUCKET_RAW,
                    content_type="video/mp4",
                )

        self.publish_status(video_id, "ingested", 1.0, details=metadata)

        self.enqueue_next("video_processing", {
            "video_id": video_id,
            "storage_path": storage_path,
            "metadata": metadata,
            "task_type": "transcode",
        })

        return {"status": "ingested", "metadata": metadata}

    async def _ingest_ip_camera(self, task: dict) -> dict:
        """Same as stream ingestion but for IP cameras."""
        return await self._ingest_stream(task)

    def _probe_video(self, filepath: str) -> dict:
        """Extract video metadata using ffprobe."""
        cmd = [
            settings.FFPROBE_PATH,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            filepath,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            self.logger.warning("ffprobe failed", stderr=result.stderr[:200])
            return {}

        probe = json.loads(result.stdout)
        video_stream = next(
            (s for s in probe.get("streams", []) if s.get("codec_type") == "video"),
            {},
        )
        fmt = probe.get("format", {})

        return {
            "duration_seconds": float(fmt.get("duration", 0)),
            "file_size_bytes": int(fmt.get("size", 0)),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "fps": eval(video_stream.get("r_frame_rate", "0/1")) if video_stream.get("r_frame_rate") else 0,
            "codec": video_stream.get("codec_name", "unknown"),
            "bitrate": int(fmt.get("bit_rate", 0)),
            "format": fmt.get("format_name", "unknown"),
        }
