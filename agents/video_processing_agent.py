"""
VideoProcessingAgent — Transcoding, stabilization, HLS generation,
thumbnail extraction, and optical correction for poolside cameras.
"""
import os
import subprocess
import tempfile
import json
from pathlib import Path

from agents.base_agent import BaseAgent
from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()


class VideoProcessingAgent(BaseAgent):
    def __init__(self):
        super().__init__("video_processing")
        self.storage = StorageService()

    async def process(self, task: dict) -> dict:
        task_type = task.get("task_type", "transcode")
        video_id = task["video_id"]

        if task_type == "transcode":
            return await self._full_pipeline(task)
        elif task_type == "stabilize":
            return await self._stabilize(task)
        elif task_type == "clip_export":
            return await self._export_clip(task)
        else:
            return await self._full_pipeline(task)

    async def _full_pipeline(self, task: dict) -> dict:
        """Full processing pipeline: transcode → stabilize → generate HLS → thumbnails."""
        video_id = task["video_id"]
        storage_path = task["storage_path"]
        metadata = task.get("metadata", {})

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input")
            self.storage.download_to_file(storage_path, input_path, bucket=settings.S3_BUCKET_RAW)

            # Step 1: Transcode to H.264 MP4 (normalized)
            self.publish_status(video_id, "transcoding", 0.1)
            transcoded_path = os.path.join(tmpdir, "transcoded.mp4")
            self._transcode(input_path, transcoded_path, metadata)
            self.publish_status(video_id, "transcoding", 0.3)

            # Step 2: Video stabilization (SteadyView)
            self.publish_status(video_id, "stabilizing", 0.35)
            stabilized_path = os.path.join(tmpdir, "stabilized.mp4")
            stabilized = self._stabilize_video(transcoded_path, stabilized_path)
            final_video = stabilized_path if stabilized else transcoded_path
            self.publish_status(video_id, "stabilizing", 0.5)

            # Step 3: Generate HLS segments for adaptive streaming
            self.publish_status(video_id, "generating_hls", 0.55)
            hls_dir = os.path.join(tmpdir, "hls")
            os.makedirs(hls_dir, exist_ok=True)
            self._generate_hls(final_video, hls_dir)
            self.publish_status(video_id, "generating_hls", 0.75)

            # Step 4: Extract thumbnail
            thumb_path = os.path.join(tmpdir, "thumbnail.jpg")
            self._extract_thumbnail(final_video, thumb_path, metadata.get("duration_seconds", 10))
            self.publish_status(video_id, "generating_hls", 0.85)

            # Step 5: Upload everything to storage
            processed_path = f"processed/{video_id}/video.mp4"
            hls_base = f"processed/{video_id}/hls"
            thumb_storage = f"thumbnails/{video_id}/thumb.jpg"

            with open(final_video, "rb") as f:
                self.storage.upload_bytes(
                    f.read(), processed_path,
                    bucket=settings.S3_BUCKET_PROCESSED,
                    content_type="video/mp4",
                )

            # Upload HLS files
            for root, dirs, files in os.walk(hls_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    rel = os.path.relpath(fpath, hls_dir)
                    ct = "application/x-mpegURL" if fname.endswith(".m3u8") else "video/MP2T"
                    with open(fpath, "rb") as f:
                        self.storage.upload_bytes(
                            f.read(), f"{hls_base}/{rel}",
                            bucket=settings.S3_BUCKET_PROCESSED,
                            content_type=ct,
                        )

            if os.path.exists(thumb_path):
                with open(thumb_path, "rb") as f:
                    self.storage.upload_bytes(
                        f.read(), thumb_storage,
                        bucket=settings.S3_BUCKET_THUMBNAILS,
                        content_type="image/jpeg",
                    )

            self.publish_status(video_id, "processed", 1.0)

        # Forward to AI detection
        self.enqueue_next("waterpolo_detection", {
            "video_id": video_id,
            "processed_path": processed_path,
            "hls_path": f"{hls_base}/master.m3u8",
            "thumbnail_path": thumb_storage,
            "metadata": metadata,
            "task_type": "detect",
        })

        return {
            "status": "processed",
            "processed_path": processed_path,
            "hls_path": f"{hls_base}/master.m3u8",
            "thumbnail_path": thumb_storage,
        }

    def _transcode(self, input_path: str, output_path: str, metadata: dict):
        """Transcode to H.264 with quality presets optimized for water polo."""
        width = metadata.get("width", 1920)
        height = metadata.get("height", 1080)

        # Determine target resolution
        if width >= 3840:
            scale = "3840:2160"
            crf = "20"
        elif width >= 1920:
            scale = "1920:1080"
            crf = "21"
        else:
            scale = f"{width}:{height}"
            crf = "22"

        cmd = [
            settings.FFMPEG_PATH,
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", crf,
            "-vf", f"scale={scale}:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if result.returncode != 0:
            self.logger.warning("Transcode error", stderr=result.stderr[:300])

    def _stabilize_video(self, input_path: str, output_path: str) -> bool:
        """Two-pass video stabilization using FFmpeg's vidstab filter.
        Especially important for poolside handheld cameras."""
        try:
            transforms_path = input_path + ".trf"

            # Pass 1: Detect shakiness
            cmd1 = [
                settings.FFMPEG_PATH,
                "-i", input_path,
                "-vf", f"vidstabdetect=shakiness=7:accuracy=15:result={transforms_path}",
                "-f", "null", "-",
            ]
            r1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=3600)
            if r1.returncode != 0:
                self.logger.warning("Stabilization detect failed", stderr=r1.stderr[:200])
                return False

            # Pass 2: Apply stabilization
            cmd2 = [
                settings.FFMPEG_PATH,
                "-i", input_path,
                "-vf", f"vidstabtransform=input={transforms_path}:smoothing=20:zoom=1:interpol=bicubic,unsharp=5:5:0.8:3:3:0.4",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "21",
                "-c:a", "copy",
                "-y",
                output_path,
            ]
            r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=3600)
            if r2.returncode != 0:
                self.logger.warning("Stabilization transform failed", stderr=r2.stderr[:200])
                return False

            return True
        except Exception as e:
            self.logger.warning("Stabilization failed", error=str(e))
            return False

    def _generate_hls(self, input_path: str, output_dir: str):
        """Generate multi-bitrate HLS for adaptive streaming."""
        # Generate multiple quality levels
        variants = [
            {"height": 360, "bitrate": "800k", "maxrate": "856k", "bufsize": "1200k"},
            {"height": 480, "bitrate": "1400k", "maxrate": "1498k", "bufsize": "2100k"},
            {"height": 720, "bitrate": "2800k", "maxrate": "2996k", "bufsize": "4200k"},
            {"height": 1080, "bitrate": "5000k", "maxrate": "5350k", "bufsize": "7500k"},
        ]

        master_playlist = "#EXTM3U\n#EXT-X-VERSION:3\n"

        for v in variants:
            variant_dir = os.path.join(output_dir, f"{v['height']}p")
            os.makedirs(variant_dir, exist_ok=True)

            cmd = [
                settings.FFMPEG_PATH,
                "-i", input_path,
                "-vf", f"scale=-2:{v['height']}",
                "-c:v", "libx264",
                "-b:v", v["bitrate"],
                "-maxrate", v["maxrate"],
                "-bufsize", v["bufsize"],
                "-c:a", "aac",
                "-b:a", "128k",
                "-hls_time", str(settings.HLS_SEGMENT_DURATION),
                "-hls_playlist_type", "vod",
                "-hls_segment_filename", os.path.join(variant_dir, "seg_%03d.ts"),
                "-y",
                os.path.join(variant_dir, "playlist.m3u8"),
            ]
            subprocess.run(cmd, capture_output=True, timeout=7200)

            bandwidth = int(v["bitrate"].replace("k", "")) * 1000
            master_playlist += (
                f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},"
                f"RESOLUTION={int(v['height'] * 16 / 9)}x{v['height']}\n"
                f"{v['height']}p/playlist.m3u8\n"
            )

        with open(os.path.join(output_dir, "master.m3u8"), "w") as f:
            f.write(master_playlist)

    def _extract_thumbnail(self, input_path: str, output_path: str, duration: float):
        """Extract a representative thumbnail frame."""
        seek_time = min(duration * 0.1, 30)  # 10% into the video, max 30s
        cmd = [
            settings.FFMPEG_PATH,
            "-ss", str(seek_time),
            "-i", input_path,
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)

    async def _stabilize(self, task: dict) -> dict:
        """Standalone stabilization task."""
        video_id = task["video_id"]
        storage_path = task["storage_path"]

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.mp4")
            output_path = os.path.join(tmpdir, "stabilized.mp4")
            self.storage.download_to_file(storage_path, input_path, bucket=settings.S3_BUCKET_PROCESSED)

            success = self._stabilize_video(input_path, output_path)
            if success:
                with open(output_path, "rb") as f:
                    self.storage.upload_bytes(
                        f.read(), storage_path,
                        bucket=settings.S3_BUCKET_PROCESSED,
                        content_type="video/mp4",
                    )

        return {"status": "stabilized" if success else "stabilization_failed"}

    async def _export_clip(self, task: dict) -> dict:
        """Export a clip from a video."""
        video_id = task["video_id"]
        clip_id = task["clip_id"]
        start_ms = task["start_ms"]
        end_ms = task["end_ms"]
        quality = task.get("quality", "1080p")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.mp4")
            output_path = os.path.join(tmpdir, f"clip_{clip_id}.mp4")

            processed_path = f"processed/{video_id}/video.mp4"
            self.storage.download_to_file(processed_path, input_path, bucket=settings.S3_BUCKET_PROCESSED)

            start_s = start_ms / 1000
            duration_s = (end_ms - start_ms) / 1000

            height_map = {"360p": 360, "480p": 480, "720p": 720, "1080p": 1080, "4k": 2160}
            height = height_map.get(quality, 1080)

            cmd = [
                settings.FFMPEG_PATH,
                "-ss", str(start_s),
                "-i", input_path,
                "-t", str(duration_s),
                "-vf", f"scale=-2:{height}",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "21",
                "-c:a", "aac",
                "-movflags", "+faststart",
                "-y",
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=600)

            clip_storage = f"clips/{clip_id}/clip.mp4"
            with open(output_path, "rb") as f:
                self.storage.upload_bytes(
                    f.read(), clip_storage,
                    bucket=settings.S3_BUCKET_CLIPS,
                    content_type="video/mp4",
                )

        return {"status": "exported", "clip_path": clip_storage}
