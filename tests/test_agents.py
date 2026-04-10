"""Unit tests for AI agents."""
import pytest
import numpy as np
from agents.analytics_engine_agent import AnalyticsEngineAgent
from agents.clip_generation_agent import ClipGenerationAgent, CLIP_PADDING
from agents.waterpolo_detection_agent import WaterpoloStateTracker, Detection


class TestAnalyticsEngine:
    def setup_method(self):
        self.agent = AnalyticsEngineAgent.__new__(AnalyticsEngineAgent)

    def test_possession_computation(self):
        ball = [{"frame": i, "class_name": "ball", "pool_x": 0.3, "pool_y": 0.5} for i in range(100)]
        dark = [{"frame": i, "class_name": "player_dark", "pool_x": 0.31, "pool_y": 0.51} for i in range(100)]
        white = [{"frame": i, "class_name": "player_white", "pool_x": 0.7, "pool_y": 0.5} for i in range(100)]

        result = self.agent._compute_possession(ball, dark, white)
        assert result["home_pct"] > 50
        assert result["home_pct"] + result["away_pct"] == 100.0

    def test_momentum_timeline(self):
        events = [
            {"event_type": "goal", "timestamp_ms": 5000, "period": "Q1",
             "details": {"scoring_team": "home"}, "position_x": 0.95, "position_y": 0.5},
            {"event_type": "goal", "timestamp_ms": 120000, "period": "Q2",
             "details": {"scoring_team": "away"}, "position_x": 0.05, "position_y": 0.5},
        ]
        timeline = self.agent._compute_momentum(events)
        assert isinstance(timeline, list)
        assert all("timestamp_ms" in e and "momentum" in e for e in timeline)

    def test_shot_map_extraction(self):
        events = [
            {"event_type": "goal", "timestamp_ms": 1000, "period": "Q1",
             "position_x": 0.9, "position_y": 0.5, "details": {}},
            {"event_type": "shot_on_target", "timestamp_ms": 2000, "period": "Q1",
             "position_x": 0.8, "position_y": 0.4, "details": {}},
        ]
        shots = self.agent._compute_shot_map(events)
        assert len(shots) == 2
        assert shots[0]["outcome"] == "goal"

    def test_heatmap_dimensions(self):
        dark = [{"pool_x": np.random.rand(), "pool_y": np.random.rand()} for _ in range(50)]
        white = [{"pool_x": np.random.rand(), "pool_y": np.random.rand()} for _ in range(50)]
        result = self.agent._compute_heatmaps(dark, white, {})
        assert len(result["home"]) == 20
        assert len(result["home"][0]) == 30
        assert result["resolution"] == {"x": 30, "y": 20}


class TestClipGeneration:
    def test_all_event_types_have_padding(self):
        important = ["goal", "shot_on_target", "exclusion", "power_play_start", "counterattack", "save"]
        for et in important:
            assert et in CLIP_PADDING, f"Missing padding for {et}"

    def test_clip_titles(self):
        agent = ClipGenerationAgent.__new__(ClipGenerationAgent)
        event = {"event_type": "goal", "period": "Q1"}
        title = agent._generate_clip_title(event)
        assert "Q1" in title

    def test_ability_labels(self):
        agent = ClipGenerationAgent.__new__(ClipGenerationAgent)
        labels = agent._suggest_ability_labels({"event_type": "save"})
        assert "goalkeeping" in labels
        labels2 = agent._suggest_ability_labels({"event_type": "counterattack"})
        assert "speed" in labels2


class TestStateTracker:
    def test_period_detection(self):
        tracker = WaterpoloStateTracker(fps=25.0)
        assert tracker.current_period == "Q1"

    def test_no_crash_empty_frame(self):
        tracker = WaterpoloStateTracker(fps=25.0)
        events = tracker.update([], 0, 0.0, 25.0)
        assert isinstance(events, list)

    def test_ball_history_updates(self):
        tracker = WaterpoloStateTracker(fps=25.0)
        det = Detection(frame=0, timestamp_ms=0, class_name="ball",
                       confidence=0.9, bbox=[0.4, 0.4, 0.5, 0.5], pool_x=0.45, pool_y=0.45)
        tracker.update([det], 0, 0.0, 25.0)
        assert len(tracker.ball_history) == 1
