import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MatchAnalytics(Base):
    __tablename__ = "match_analytics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), unique=True, nullable=False
    )

    # Possession
    home_possession_pct: Mapped[float] = mapped_column(Float, default=50.0)
    away_possession_pct: Mapped[float] = mapped_column(Float, default=50.0)
    possession_timeline: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # [{timestamp_ms, team: "home"|"away"}]

    # Shots
    home_shots: Mapped[int] = mapped_column(Integer, default=0)
    away_shots: Mapped[int] = mapped_column(Integer, default=0)
    home_shots_on_target: Mapped[int] = mapped_column(Integer, default=0)
    away_shots_on_target: Mapped[int] = mapped_column(Integer, default=0)

    # Power play
    home_power_play_attempts: Mapped[int] = mapped_column(Integer, default=0)
    home_power_play_goals: Mapped[int] = mapped_column(Integer, default=0)
    away_power_play_attempts: Mapped[int] = mapped_column(Integer, default=0)
    away_power_play_goals: Mapped[int] = mapped_column(Integer, default=0)

    # Exclusions
    home_exclusions: Mapped[int] = mapped_column(Integer, default=0)
    away_exclusions: Mapped[int] = mapped_column(Integer, default=0)

    # Momentum: [{timestamp_ms, momentum: -100 to 100}]
    momentum_timeline: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Per-quarter breakdown
    quarter_stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # {Q1: {home_goals, away_goals, home_possession, ...}, ...}

    # Coach AI summary
    ai_summary: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    ai_talking_points: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_recommendations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    match = relationship("Match", back_populates="analytics")


class PlayerMatchStats(Base):
    __tablename__ = "player_match_stats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )

    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    shots: Mapped[int] = mapped_column(Integer, default=0)
    shots_on_target: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    exclusions_drawn: Mapped[int] = mapped_column(Integer, default=0)
    exclusions_committed: Mapped[int] = mapped_column(Integer, default=0)
    steals: Mapped[int] = mapped_column(Integer, default=0)
    turnovers: Mapped[int] = mapped_column(Integer, default=0)
    power_play_goals: Mapped[int] = mapped_column(Integer, default=0)
    blocks: Mapped[int] = mapped_column(Integer, default=0)
    sprints: Mapped[int] = mapped_column(Integer, default=0)
    distance_swum_m: Mapped[float] = mapped_column(Float, default=0.0)
    minutes_played: Mapped[float] = mapped_column(Float, default=0.0)

    # Heatmap data: [[x, y, intensity], ...]
    heatmap_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    player = relationship("Player", back_populates="match_stats")


class ShotRecord(Base):
    __tablename__ = "shot_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=True
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_events.id"), nullable=True
    )
    period: Mapped[str] = mapped_column(String(5), nullable=False)
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    shot_x: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1 pool coords
    shot_y: Mapped[float] = mapped_column(Float, nullable=False)
    target_x: Mapped[float | None] = mapped_column(Float, nullable=True)  # goal zone
    target_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)  # goal/saved/blocked/missed
    shot_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # backhand/skip/lob/direct
    is_power_play: Mapped[bool] = mapped_column(default=False)
    is_penalty: Mapped[bool] = mapped_column(default=False)
    speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)


class PassRecord(Base):
    __tablename__ = "pass_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    from_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=True
    )
    to_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=True
    )
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    from_x: Mapped[float] = mapped_column(Float, nullable=False)
    from_y: Mapped[float] = mapped_column(Float, nullable=False)
    to_x: Mapped[float] = mapped_column(Float, nullable=False)
    to_y: Mapped[float] = mapped_column(Float, nullable=False)
    is_successful: Mapped[bool] = mapped_column(default=True)
    is_assist: Mapped[bool] = mapped_column(default=False)


class PossessionRecord(Base):
    __tablename__ = "possession_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[str] = mapped_column(String(5), nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)  # goal/shot/turnover/clock


class HeatmapData(Base):
    __tablename__ = "heatmap_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
    period: Mapped[str | None] = mapped_column(String(5), nullable=True)
    # Grid data: 30x20 grid matching pool dimensions
    grid_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    resolution_x: Mapped[int] = mapped_column(Integer, default=30)
    resolution_y: Mapped[int] = mapped_column(Integer, default=20)
