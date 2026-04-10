"""
AnalyticsEngineAgent — Computes all match statistics from detection results.

Generates: possession %, shot maps, heatmaps, pass networks, power play
efficiency, match momentum, per-quarter breakdown, and player stats.
"""
import json
import numpy as np
from collections import defaultdict

from agents.base_agent import BaseAgent
from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()


class AnalyticsEngineAgent(BaseAgent):
    def __init__(self):
        super().__init__("analytics_engine")
        self.storage = StorageService()

    async def process(self, task: dict) -> dict:
        video_id = task["video_id"]
        match_id = task.get("match_id")
        results_path = task["results_path"]

        self.publish_status(video_id, "computing_analytics", 0.0)

        # Load detection results
        raw = self.storage.download_file(results_path, bucket=settings.S3_BUCKET_PROCESSED)
        data = json.loads(raw)
        detections = data.get("detections", [])
        events = data.get("events", [])
        tracking_data = data.get("tracking_data", {})

        analytics = self._compute_all(detections, events, tracking_data, match_id)

        # Save analytics
        analytics_path = f"analysis/{video_id}/analytics.json"
        self.storage.upload_bytes(
            json.dumps(analytics).encode(),
            analytics_path,
            bucket=settings.S3_BUCKET_PROCESSED,
            content_type="application/json",
        )

        self.publish_status(video_id, "analytics_ready", 1.0)

        # Forward to clip generation
        self.enqueue_next("clip_generation", {
            "video_id": video_id,
            "match_id": match_id,
            "events": events,
            "analytics_path": analytics_path,
            "hls_path": task.get("hls_path"),
            "thumbnail_path": task.get("thumbnail_path"),
            "task_type": "auto_clips",
        })

        # If match_id provided, persist to DB
        if match_id:
            self.enqueue_next("db_writer", {
                "task_type": "write_analytics",
                "video_id": video_id,
                "match_id": match_id,
                "analytics_path": analytics_path,
                "hls_path": task.get("hls_path"),
                "thumbnail_path": task.get("thumbnail_path"),
            })

        return {"status": "computed", "analytics_path": analytics_path}

    def _compute_all(self, detections, events, tracking_data, match_id) -> dict:
        """Compute all analytics from raw detection data."""
        ball_detections = [d for d in detections if d["class_name"] == "ball"]
        dark_detections = [d for d in detections if d["class_name"] == "player_dark"]
        white_detections = [d for d in detections if d["class_name"] == "player_white"]

        possession = self._compute_possession(ball_detections, dark_detections, white_detections)
        shot_map = self._compute_shot_map(events)
        heatmaps = self._compute_heatmaps(dark_detections, white_detections, tracking_data)
        momentum = self._compute_momentum(events)
        quarter_stats = self._compute_quarter_stats(events)
        power_play_stats = self._compute_power_play(events)
        player_stats = self._compute_player_stats(events, tracking_data)

        return {
            "match_id": match_id,
            "possession": possession,
            "shot_map": shot_map,
            "heatmaps": heatmaps,
            "momentum_timeline": momentum,
            "quarter_stats": quarter_stats,
            "power_play": power_play_stats,
            "player_stats": player_stats,
            "event_counts": self._count_events(events),
        }

    def _compute_possession(self, ball_dets, dark_dets, white_dets) -> dict:
        """Estimate possession by proximity of ball to each team."""
        dark_possession = 0
        white_possession = 0

        ball_by_frame = {d["frame"]: d for d in ball_dets}
        dark_by_frame = defaultdict(list)
        white_by_frame = defaultdict(list)
        for d in dark_dets:
            dark_by_frame[d["frame"]].append(d)
        for d in white_dets:
            white_by_frame[d["frame"]].append(d)

        for frame, ball in ball_by_frame.items():
            bx, by = ball.get("pool_x", 0.5), ball.get("pool_y", 0.5)

            min_dark = min(
                (((p.get("pool_x", 0.5) - bx)**2 + (p.get("pool_y", 0.5) - by)**2)**0.5
                 for p in dark_by_frame[frame]),
                default=999,
            )
            min_white = min(
                (((p.get("pool_x", 0.5) - bx)**2 + (p.get("pool_y", 0.5) - by)**2)**0.5
                 for p in white_by_frame[frame]),
                default=999,
            )

            if min_dark < min_white:
                dark_possession += 1
            elif min_white < min_dark:
                white_possession += 1

        total = dark_possession + white_possession or 1
        return {
            "home_pct": round(dark_possession / total * 100, 1),
            "away_pct": round(white_possession / total * 100, 1),
            "home_frames": dark_possession,
            "away_frames": white_possession,
        }

    def _compute_shot_map(self, events) -> list:
        shots = []
        for e in events:
            if e["event_type"] in ("goal", "shot_on_target", "shot_off_target", "shot_blocked"):
                shots.append({
                    "timestamp_ms": e["timestamp_ms"],
                    "period": e["period"],
                    "x": e.get("position_x", 0.5),
                    "y": e.get("position_y", 0.5),
                    "outcome": "goal" if e["event_type"] == "goal" else "saved",
                    "is_power_play": e.get("details", {}).get("is_power_play", False),
                })
        return shots

    def _compute_heatmaps(self, dark_dets, white_dets, tracking_data) -> dict:
        """Build 30×20 position heatmaps for each team."""
        grid_x, grid_y = 30, 20

        home_grid = np.zeros((grid_y, grid_x), dtype=float)
        away_grid = np.zeros((grid_y, grid_x), dtype=float)

        for d in dark_dets:
            if d.get("pool_x") and d.get("pool_y"):
                xi = min(int(d["pool_x"] * grid_x), grid_x - 1)
                yi = min(int(d["pool_y"] * grid_y), grid_y - 1)
                home_grid[yi][xi] += 1

        for d in white_dets:
            if d.get("pool_x") and d.get("pool_y"):
                xi = min(int(d["pool_x"] * grid_x), grid_x - 1)
                yi = min(int(d["pool_y"] * grid_y), grid_y - 1)
                away_grid[yi][xi] += 1

        # Normalize to 0-1
        if home_grid.max() > 0:
            home_grid = home_grid / home_grid.max()
        if away_grid.max() > 0:
            away_grid = away_grid / away_grid.max()

        return {
            "home": home_grid.tolist(),
            "away": away_grid.tolist(),
            "resolution": {"x": grid_x, "y": grid_y},
        }

    def _compute_momentum(self, events) -> list:
        """Compute match momentum timeline: positive = home advantage."""
        if not events:
            return []

        max_ts = max(e["timestamp_ms"] for e in events)
        window = 60000  # 60-second rolling window
        step = 10000    # 10-second steps

        timeline = []
        for ts in range(0, int(max_ts) + step, step):
            window_events = [
                e for e in events
                if ts - window <= e["timestamp_ms"] <= ts
            ]

            home_score = sum(
                1 for e in window_events
                if e["event_type"] == "goal" and
                e.get("details", {}).get("scoring_team") == "home"
            )
            away_score = sum(
                1 for e in window_events
                if e["event_type"] == "goal" and
                e.get("details", {}).get("scoring_team") == "away"
            )
            home_shots = sum(1 for e in window_events if e["event_type"] in ("shot_on_target", "goal"))
            away_shots = sum(1 for e in window_events if e["event_type"] in ("shot_on_target",))
            home_pp = sum(1 for e in window_events if e["event_type"] == "power_play_start" and
                         e.get("details", {}).get("advantage_team") == "dark")

            momentum = (
                (home_score - away_score) * 20 +
                (home_shots - away_shots) * 5 +
                home_pp * 10
            )
            timeline.append({
                "timestamp_ms": ts,
                "momentum": max(-100, min(100, momentum)),
            })

        return timeline

    def _compute_quarter_stats(self, events) -> dict:
        stats = {}
        for period in ["Q1", "Q2", "Q3", "Q4", "OT1", "OT2"]:
            period_events = [e for e in events if e["period"] == period]
            if not period_events:
                continue
            stats[period] = {
                "home_goals": sum(1 for e in period_events if e["event_type"] == "goal"
                                 and e.get("details", {}).get("scoring_team") == "home"),
                "away_goals": sum(1 for e in period_events if e["event_type"] == "goal"
                                 and e.get("details", {}).get("scoring_team") == "away"),
                "home_shots": sum(1 for e in period_events if e["event_type"] in ("shot_on_target", "goal")),
                "away_shots": sum(1 for e in period_events if e["event_type"] == "shot_on_target"),
                "power_plays": sum(1 for e in period_events if e["event_type"] == "power_play_start"),
                "counterattacks": sum(1 for e in period_events if e["event_type"] == "counterattack"),
            }
        return stats

    def _compute_power_play(self, events) -> dict:
        pp_starts = [e for e in events if e["event_type"] == "power_play_start"]
        total = len(pp_starts)
        scored = sum(1 for e in events if e["event_type"] == "goal")  # simplified
        return {
            "total_opportunities": total,
            "goals_scored": scored,
            "efficiency_pct": round(scored / total * 100, 1) if total > 0 else 0,
        }

    def _compute_player_stats(self, events, tracking_data) -> dict:
        player_stats = defaultdict(lambda: {
            "shots": 0, "goals": 0, "counterattacks": 0,
            "distances_traveled": 0.0,
        })
        for e in events:
            tid = str(e.get("player_track_id", ""))
            if not tid:
                continue
            et = e["event_type"]
            if et in ("shot_on_target", "goal", "shot_blocked", "shot_off_target"):
                player_stats[tid]["shots"] += 1
            if et == "goal":
                player_stats[tid]["goals"] += 1
            if et == "counterattack":
                player_stats[tid]["counterattacks"] += 1

        for tid, track in tracking_data.items():
            positions = track.get("positions", [])
            dist = 0.0
            for i in range(1, len(positions)):
                dx = (positions[i].get("x") or 0) - (positions[i-1].get("x") or 0)
                dy = (positions[i].get("y") or 0) - (positions[i-1].get("y") or 0)
                dist += (dx**2 + dy**2)**0.5
            player_stats[str(tid)]["distances_traveled"] = round(dist * 30, 2)  # approximate meters (30m pool)

        return dict(player_stats)

    def _count_events(self, events) -> dict:
        counts = defaultdict(int)
        for e in events:
            counts[e["event_type"]] += 1
        return dict(counts)
