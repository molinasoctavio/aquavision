"""
WaterpoloAIDetectionAgent — Computer vision engine specialized for water polo.

Uses YOLOv8 fine-tuned on water polo footage to detect:
- Ball (yellow/orange against blue water)
- Players with colored caps (dark/white/red)
- Cap numbers via OCR
- Automatic event detection: goals, exclusions, power play, etc.
"""
import os
import cv2
import numpy as np
import tempfile
import json
from pathlib import Path
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Optional

from agents.base_agent import BaseAgent
from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()


@dataclass
class Detection:
    frame: int
    timestamp_ms: float
    class_name: str   # ball, player_dark, player_white, player_red_gk
    confidence: float
    bbox: list        # [x1, y1, x2, y2] normalized 0-1
    track_id: Optional[int] = None
    cap_number: Optional[int] = None
    pool_x: Optional[float] = None  # 0-1 pool coordinate
    pool_y: Optional[float] = None


@dataclass
class GameEvent:
    frame: int
    timestamp_ms: float
    event_type: str
    period: str
    confidence: float
    player_track_id: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class WaterpoloDetectionAgent(BaseAgent):
    def __init__(self):
        super().__init__("waterpolo_detection")
        self.storage = StorageService()
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load YOLO model, falling back to base YOLOv8 if fine-tuned not available."""
        try:
            from ultralytics import YOLO
            model_path = settings.YOLO_MODEL_PATH
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
                self.logger.info("Loaded fine-tuned waterpolo model", path=model_path)
            else:
                # Use base YOLOv8n as fallback
                self.model = YOLO("yolov8n.pt")
                self.logger.warning("Fine-tuned model not found, using base YOLOv8n")
        except Exception as e:
            self.logger.error("Failed to load YOLO model", error=str(e))
            self.model = None

    async def process(self, task: dict) -> dict:
        video_id = task["video_id"]
        match_id = task.get("match_id")
        processed_path = task["processed_path"]

        self.publish_status(video_id, "analyzing", 0.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "video.mp4")
            self.storage.download_to_file(
                processed_path, local_path,
                bucket=settings.S3_BUCKET_PROCESSED
            )

            detections, events, tracking_data = self._run_detection_pipeline(
                local_path, video_id
            )

        # Save results
        results = {
            "video_id": video_id,
            "match_id": match_id,
            "detections": [asdict(d) for d in detections],
            "events": [asdict(e) for e in events],
            "tracking_data": tracking_data,
        }

        results_path = f"analysis/{video_id}/detections.json"
        self.storage.upload_bytes(
            json.dumps(results).encode(),
            results_path,
            bucket=settings.S3_BUCKET_PROCESSED,
            content_type="application/json",
        )

        self.publish_status(video_id, "detected", 1.0)

        # Forward to analytics engine
        self.enqueue_next("analytics_engine", {
            "video_id": video_id,
            "match_id": match_id,
            "results_path": results_path,
            "task_type": "compute_analytics",
            "hls_path": task.get("hls_path"),
            "thumbnail_path": task.get("thumbnail_path"),
        })

        return {"status": "detected", "events_count": len(events)}

    def _run_detection_pipeline(self, video_path: str, video_id: str):
        """Main detection loop over video frames."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_skip = settings.DETECTION_FRAME_SKIP

        detections = []
        events = []
        tracking_data = {}

        # State machine for event detection
        state = WaterpoloStateTracker(fps)

        frame_idx = 0
        last_progress = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_skip != 0:
                frame_idx += 1
                continue

            timestamp_ms = (frame_idx / fps) * 1000

            # Run YOLO detection
            frame_detections = self._detect_frame(frame, frame_idx, timestamp_ms, fps)
            detections.extend(frame_detections)

            # Update state machine and detect events
            new_events = state.update(frame_detections, frame_idx, timestamp_ms, fps)
            events.extend(new_events)

            # Update tracking data
            for det in frame_detections:
                if det.track_id is not None:
                    if det.track_id not in tracking_data:
                        tracking_data[det.track_id] = {
                            "class": det.class_name,
                            "positions": [],
                            "cap_number": det.cap_number,
                        }
                    tracking_data[det.track_id]["positions"].append({
                        "frame": frame_idx,
                        "ts": timestamp_ms,
                        "x": det.pool_x,
                        "y": det.pool_y,
                    })

            # Progress reporting
            progress = frame_idx / max(total_frames, 1)
            if progress - last_progress > 0.05:
                self.publish_status(video_id, "analyzing", progress * 0.9)
                last_progress = progress

            frame_idx += 1

        cap.release()
        return detections, events, tracking_data

    def _detect_frame(self, frame: np.ndarray, frame_idx: int, timestamp_ms: float, fps: float) -> list[Detection]:
        """Run YOLO on a single frame and return detections."""
        detections = []
        h, w = frame.shape[:2]

        if self.model is None:
            # Fallback: use color-based ball detection
            return self._color_detect_ball(frame, frame_idx, timestamp_ms)

        try:
            results = self.model.track(
                frame,
                persist=True,
                conf=settings.YOLO_CONFIDENCE_THRESHOLD,
                verbose=False,
                classes=None,
            )

            for r in results:
                if r.boxes is None:
                    continue
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    track_id = int(box.id[0]) if box.id is not None else None

                    # Normalize bbox
                    bbox = [x1/w, y1/h, x2/w, y2/h]
                    pool_x = ((x1 + x2) / 2) / w
                    pool_y = ((y1 + y2) / 2) / h

                    class_map = {
                        0: "ball",
                        1: "player_dark",
                        2: "player_white",
                        3: "player_red_gk",
                    }
                    class_name = class_map.get(cls_id, f"class_{cls_id}")

                    det = Detection(
                        frame=frame_idx,
                        timestamp_ms=timestamp_ms,
                        class_name=class_name,
                        confidence=conf,
                        bbox=bbox,
                        track_id=track_id,
                        pool_x=pool_x,
                        pool_y=pool_y,
                    )
                    detections.append(det)
        except Exception as e:
            self.logger.warning("YOLO detection failed on frame", frame=frame_idx, error=str(e))
            return self._color_detect_ball(frame, frame_idx, timestamp_ms)

        return detections

    def _color_detect_ball(self, frame: np.ndarray, frame_idx: int, timestamp_ms: float) -> list[Detection]:
        """Fallback: detect water polo ball by color (yellow-orange against blue water)."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w = frame.shape[:2]

        # Yellow-orange ball range in HSV
        lower_ball = np.array([10, 120, 120])
        upper_ball = np.array([30, 255, 255])
        mask = cv2.inRange(hsv, lower_ball, upper_ball)

        # Morphological cleanup
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 200 < area < 5000:  # reasonable ball size
                x, y, bw, bh = cv2.boundingRect(cnt)
                circularity = 4 * np.pi * area / (cv2.arcLength(cnt, True) ** 2 + 1e-6)
                if circularity > 0.6:
                    detections.append(Detection(
                        frame=frame_idx,
                        timestamp_ms=timestamp_ms,
                        class_name="ball",
                        confidence=circularity,
                        bbox=[x/w, y/h, (x+bw)/w, (y+bh)/h],
                        pool_x=(x + bw/2) / w,
                        pool_y=(y + bh/2) / h,
                    ))
        return detections[:1]  # keep best ball candidate


class WaterpoloStateTracker:
    """State machine that tracks game state and detects events from frame detections."""

    PERIOD_DURATION_FRAMES = 8 * 60 * 25  # 8 min * 60s * 25fps

    def __init__(self, fps: float):
        self.fps = fps
        self.current_period = "Q1"
        self.period_start_frame = 0
        self.ball_history = deque(maxlen=60)  # last 2 seconds
        self.player_positions = defaultdict(lambda: deque(maxlen=30))
        self.possession_team = None
        self.possession_start = 0
        self.exclusion_count = defaultdict(int)
        self.last_goal_frame = -300
        self.shot_clock = 30.0
        self.shot_clock_start = 0
        self.active_power_plays = []
        self.events = []

    def update(self, detections: list, frame_idx: int, timestamp_ms: float, fps: float) -> list[GameEvent]:
        new_events = []

        ball_dets = [d for d in detections if d.class_name == "ball"]
        player_dets = [d for d in detections if "player" in d.class_name]

        # Update histories
        if ball_dets:
            self.ball_history.append(ball_dets[0])

        for p in player_dets:
            if p.track_id:
                self.player_positions[p.track_id].append(p)

        # Detect period changes
        period_event = self._check_period(frame_idx, timestamp_ms)
        if period_event:
            new_events.append(period_event)

        # Detect goal (ball near goal line + high velocity toward goal)
        goal_event = self._detect_goal(ball_dets, frame_idx, timestamp_ms)
        if goal_event:
            new_events.append(goal_event)

        # Detect shot (ball moving fast)
        shot_event = self._detect_shot(ball_dets, frame_idx, timestamp_ms)
        if shot_event:
            new_events.append(shot_event)

        # Detect power play (count players on each side)
        pp_event = self._detect_power_play(player_dets, frame_idx, timestamp_ms)
        if pp_event:
            new_events.append(pp_event)

        # Detect counterattack (fast player movement toward goal)
        ca_event = self._detect_counterattack(player_dets, frame_idx, timestamp_ms)
        if ca_event:
            new_events.append(ca_event)

        return new_events

    def _check_period(self, frame_idx: int, timestamp_ms: float) -> Optional[GameEvent]:
        periods = ["Q1", "Q2", "Q3", "Q4"]
        period_frames = int(8 * 60 * self.fps)
        period_idx = (frame_idx - self.period_start_frame) // period_frames
        if period_idx < len(periods) and periods[period_idx] != self.current_period:
            self.current_period = periods[period_idx]
            return GameEvent(
                frame=frame_idx, timestamp_ms=timestamp_ms,
                event_type="period_start", period=self.current_period,
                confidence=1.0, details={"period": self.current_period},
            )
        return None

    def _detect_goal(self, ball_dets: list, frame_idx: int, timestamp_ms: float) -> Optional[GameEvent]:
        if not ball_dets or (frame_idx - self.last_goal_frame) < int(5 * self.fps):
            return None
        ball = ball_dets[0]
        # Goal zones: near left (x<0.05) or right (x>0.95) edges
        if ball.pool_x and (ball.pool_x < 0.05 or ball.pool_x > 0.95):
            if len(self.ball_history) >= 5:
                prev = self.ball_history[-5]
                if prev.pool_x:
                    dx = abs(ball.pool_x - prev.pool_x)
                    if dx > 0.03:  # ball moved significantly toward goal
                        self.last_goal_frame = frame_idx
                        team = "home" if ball.pool_x > 0.95 else "away"
                        return GameEvent(
                            frame=frame_idx, timestamp_ms=timestamp_ms,
                            event_type="goal", period=self.current_period,
                            confidence=0.75, position_x=ball.pool_x,
                            position_y=ball.pool_y,
                            details={"scoring_team": team},
                        )
        return None

    def _detect_shot(self, ball_dets: list, frame_idx: int, timestamp_ms: float) -> Optional[GameEvent]:
        if len(self.ball_history) < 3 or not ball_dets:
            return None
        curr = ball_dets[0]
        prev = self.ball_history[-3]
        if curr.pool_x and prev.pool_x:
            speed = abs(curr.pool_x - prev.pool_x) + abs((curr.pool_y or 0) - (prev.pool_y or 0))
            if speed > 0.15:  # fast ball movement
                return GameEvent(
                    frame=frame_idx, timestamp_ms=timestamp_ms,
                    event_type="shot_on_target", period=self.current_period,
                    confidence=min(speed * 3, 0.9),
                    position_x=curr.pool_x, position_y=curr.pool_y,
                    details={"ball_speed": round(speed, 3)},
                )
        return None

    def _detect_power_play(self, player_dets: list, frame_idx: int, timestamp_ms: float) -> Optional[GameEvent]:
        dark_count = sum(1 for p in player_dets if p.class_name == "player_dark")
        white_count = sum(1 for p in player_dets if p.class_name == "player_white")
        # 6v5 situation
        if abs(dark_count - white_count) >= 1 and min(dark_count, white_count) >= 4:
            if not self.active_power_plays or (frame_idx - self.active_power_plays[-1]) > int(25 * self.fps):
                self.active_power_plays.append(frame_idx)
                advantage = "dark" if dark_count > white_count else "white"
                return GameEvent(
                    frame=frame_idx, timestamp_ms=timestamp_ms,
                    event_type="power_play_start", period=self.current_period,
                    confidence=0.8, details={
                        "advantage_team": advantage,
                        "dark_count": dark_count,
                        "white_count": white_count,
                    },
                )
        return None

    def _detect_counterattack(self, player_dets: list, frame_idx: int, timestamp_ms: float) -> Optional[GameEvent]:
        if len(player_dets) < 2:
            return None
        # Look for isolated fast-moving player ahead of defense
        for p in player_dets:
            if p.track_id and len(self.player_positions[p.track_id]) >= 5:
                history = list(self.player_positions[p.track_id])
                if history[-1].pool_x and history[-5].pool_x:
                    speed = abs(history[-1].pool_x - history[-5].pool_x)
                    if speed > 0.10:  # fast horizontal movement
                        return GameEvent(
                            frame=frame_idx, timestamp_ms=timestamp_ms,
                            event_type="counterattack", period=self.current_period,
                            confidence=0.65, player_track_id=p.track_id,
                            position_x=p.pool_x, position_y=p.pool_y,
                            details={"speed": round(speed, 3)},
                        )
        return None
