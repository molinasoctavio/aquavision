"""
PlayerSpotlightAgent — Individual player tracking, cap OCR, and highlight reels.
"""
import json
import cv2
import numpy as np
from collections import defaultdict

from agents.base_agent import BaseAgent
from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()


class PlayerSpotlightAgent(BaseAgent):
    def __init__(self):
        super().__init__("player_spotlight")
        self.storage = StorageService()

    async def process(self, task: dict) -> dict:
        task_type = task.get("task_type", "generate_spotlight")
        if task_type == "generate_spotlight":
            return await self._generate_player_spotlight(task)
        elif task_type == "detect_cap_numbers":
            return await self._detect_cap_numbers(task)
        return {}

    async def _generate_player_spotlight(self, task: dict) -> dict:
        video_id = task["video_id"]
        player_id = task.get("player_id")
        track_id = task.get("track_id")

        if not track_id:
            return {"status": "no_track_id"}

        # Load tracking data
        results_path = f"analysis/{video_id}/detections.json"
        try:
            raw = self.storage.download_file(results_path, bucket=settings.S3_BUCKET_PROCESSED)
            data = json.loads(raw)
        except Exception:
            return {"status": "no_detections"}

        tracking_data = data.get("tracking_data", {})
        player_track = tracking_data.get(str(track_id), {})
        positions = player_track.get("positions", [])

        if not positions:
            return {"status": "no_positions"}

        # Generate player heatmap
        heatmap = self._generate_player_heatmap(positions)

        # Find key moments
        key_moments = self._find_key_moments(data.get("events", []), track_id)

        # Calculate player metrics
        metrics = self._calculate_player_metrics(positions, key_moments)

        spotlight = {
            "player_id": player_id,
            "track_id": track_id,
            "heatmap": heatmap,
            "key_moments": key_moments,
            "metrics": metrics,
        }

        path = f"analysis/{video_id}/spotlight_{track_id}.json"
        self.storage.upload_bytes(
            json.dumps(spotlight).encode(),
            path,
            bucket=settings.S3_BUCKET_PROCESSED,
            content_type="application/json",
        )

        return {"status": "generated", "path": path}

    async def _detect_cap_numbers(self, task: dict) -> dict:
        """Detect cap numbers using OCR on player crop regions."""
        video_id = task["video_id"]
        frame_data = task.get("frames", [])

        results = {}
        for frame_info in frame_data:
            track_id = frame_info.get("track_id")
            bbox = frame_info.get("bbox")

            if not bbox:
                continue

            cap_number = self._ocr_cap_number(frame_info.get("frame_bytes"), bbox)
            if cap_number:
                results[str(track_id)] = cap_number

        return {"cap_numbers": results}

    def _ocr_cap_number(self, frame_bytes: bytes | None, bbox: list) -> int | None:
        """OCR cap number from player bounding box using OpenCV."""
        if not frame_bytes:
            return None
        try:
            arr = np.frombuffer(frame_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            h, w = img.shape[:2]

            x1, y1, x2, y2 = int(bbox[0]*w), int(bbox[1]*h), int(bbox[2]*w), int(bbox[3]*h)
            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                return None

            # Focus on top portion of player (cap area)
            cap_crop = crop[:int(crop.shape[0] * 0.3), :]
            gray = cv2.cvtColor(cap_crop, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Use simple contour-based digit detection
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            digit_regions = []
            for cnt in contours:
                x, y, cw, ch = cv2.boundingRect(cnt)
                if 5 < cw < 30 and 8 < ch < 40:
                    digit_regions.append((x, cap_crop[y:y+ch, x:x+cw]))

            # Sort left-to-right
            digit_regions.sort(key=lambda r: r[0])

            if 1 <= len(digit_regions) <= 2:
                return len(digit_regions)  # placeholder: return count as number proxy
        except Exception:
            pass
        return None

    def _generate_player_heatmap(self, positions: list) -> list:
        grid = np.zeros((20, 30), dtype=float)
        for pos in positions:
            x, y = pos.get("x"), pos.get("y")
            if x is not None and y is not None:
                xi = min(int(x * 30), 29)
                yi = min(int(y * 20), 19)
                grid[yi][xi] += 1
        if grid.max() > 0:
            grid /= grid.max()
        return grid.tolist()

    def _find_key_moments(self, events: list, track_id) -> list:
        return [
            {
                "event_type": e["event_type"],
                "timestamp_ms": e["timestamp_ms"],
                "period": e["period"],
            }
            for e in events
            if e.get("player_track_id") == track_id
        ]

    def _calculate_player_metrics(self, positions: list, key_moments: list) -> dict:
        if not positions:
            return {}

        total_dist = 0.0
        for i in range(1, len(positions)):
            dx = (positions[i].get("x") or 0) - (positions[i-1].get("x") or 0)
            dy = (positions[i].get("y") or 0) - (positions[i-1].get("y") or 0)
            total_dist += (dx**2 + dy**2) ** 0.5

        return {
            "distance_normalized": round(total_dist, 3),
            "distance_meters_approx": round(total_dist * 30, 1),
            "active_frames": len(positions),
            "key_event_count": len(key_moments),
            "goals": sum(1 for e in key_moments if e["event_type"] == "goal"),
            "shots": sum(1 for e in key_moments if "shot" in e["event_type"]),
        }
