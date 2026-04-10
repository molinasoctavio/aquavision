from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MatchCreate(BaseModel):
    home_team_id: str
    away_team_id: str
    tournament_id: str | None = None
    season_id: str | None = None
    scheduled_at: datetime | None = None
    venue: str | None = None
    pool_length: float = 30.0
    pool_width: float = 20.0
    period_duration: int = 480
    shot_clock: int = 30
    notes: str | None = None


class MatchResponse(BaseModel):
    id: str
    home_team_id: str
    away_team_id: str
    status: str
    scheduled_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    home_score: int
    away_score: int
    venue: str | None
    pool_length: float
    pool_width: float
    period_duration: int
    shot_clock: int
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchEventCreate(BaseModel):
    event_type: str
    period: str
    timestamp_ms: int
    game_clock_seconds: int | None = None
    player_id: str | None = None
    secondary_player_id: str | None = None
    team_id: str | None = None
    position_x: float | None = None
    position_y: float | None = None
    details: dict | None = None


class MatchEventResponse(BaseModel):
    id: str
    match_id: str
    event_type: str
    period: str
    timestamp_ms: int
    game_clock_seconds: int | None
    player_id: str | None
    team_id: str | None
    position_x: float | None
    position_y: float | None
    details: dict | None
    is_auto_detected: bool
    confidence: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
