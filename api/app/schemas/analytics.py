from pydantic import BaseModel
from datetime import datetime


class MatchAnalyticsResponse(BaseModel):
    id: str
    match_id: str
    home_possession_pct: float
    away_possession_pct: float
    home_shots: int
    away_shots: int
    home_shots_on_target: int
    away_shots_on_target: int
    home_power_play_attempts: int
    home_power_play_goals: int
    away_power_play_attempts: int
    away_power_play_goals: int
    home_exclusions: int
    away_exclusions: int
    momentum_timeline: dict | None
    quarter_stats: dict | None
    ai_summary: str | None
    ai_talking_points: dict | None
    ai_recommendations: dict | None

    model_config = {"from_attributes": True}


class PlayerMatchStatsResponse(BaseModel):
    id: str
    match_id: str
    player_id: str
    team_id: str
    goals: int
    assists: int
    shots: int
    shots_on_target: int
    saves: int
    exclusions_drawn: int
    exclusions_committed: int
    steals: int
    turnovers: int
    power_play_goals: int
    blocks: int
    sprints: int
    distance_swum_m: float
    minutes_played: float
    heatmap_data: dict | None

    model_config = {"from_attributes": True}


class ShotMapResponse(BaseModel):
    match_id: str
    shots: list[dict]
    total_shots: int
    goals: int
    saves: int
    misses: int
    blocks: int


class CoachAssistQuery(BaseModel):
    match_id: str
    question: str


class CoachAssistResponse(BaseModel):
    match_id: str
    question: str
    answer: str
    relevant_clips: list[str] | None = None
    suggested_follow_ups: list[str] | None = None
