import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, Enum, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    RECORDING = "recording"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    COMPLETED = "completed"


class EventType(str, enum.Enum):
    GOAL = "goal"
    SHOT_ON_TARGET = "shot_on_target"
    SHOT_OFF_TARGET = "shot_off_target"
    SHOT_BLOCKED = "shot_blocked"
    SAVE = "save"
    EXCLUSION = "exclusion"  # 20s major foul
    PENALTY_5M = "penalty_5m"
    PENALTY_GOAL = "penalty_goal"
    PENALTY_MISS = "penalty_miss"
    CORNER = "corner"
    GOAL_THROW = "goal_throw"
    FOUL = "foul"
    TURNOVER = "turnover"
    STEAL = "steal"
    ASSIST = "assist"
    COUNTERATTACK = "counterattack"
    POWER_PLAY_START = "power_play_start"
    POWER_PLAY_END = "power_play_end"
    TIMEOUT = "timeout"
    PERIOD_START = "period_start"
    PERIOD_END = "period_end"
    SUBSTITUTION = "substitution"
    POSSESSION_CHANGE = "possession_change"
    SPRINT = "sprint"
    PRESS = "press"
    SHOT_CLOCK_VIOLATION = "shot_clock_violation"


class MatchPeriod(str, enum.Enum):
    FIRST = "Q1"
    SECOND = "Q2"
    THIRD = "Q3"
    FOURTH = "Q4"
    OVERTIME_1 = "OT1"
    OVERTIME_2 = "OT2"
    PENALTY_SHOOTOUT = "PS"


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    home_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    away_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    tournament_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=True
    )
    season_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True
    )
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus), default=MatchStatus.SCHEDULED
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    home_score: Mapped[int] = mapped_column(Integer, default=0)
    away_score: Mapped[int] = mapped_column(Integer, default=0)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pool_length: Mapped[float] = mapped_column(Float, default=30.0)  # meters
    pool_width: Mapped[float] = mapped_column(Float, default=20.0)  # meters
    period_duration: Mapped[int] = mapped_column(Integer, default=480)  # seconds (8 min)
    shot_clock: Mapped[int] = mapped_column(Integer, default=30)  # seconds
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    videos = relationship("Video", back_populates="match")
    events = relationship("MatchEvent", back_populates="match", order_by="MatchEvent.timestamp_ms")
    clips = relationship("Clip", back_populates="match")
    analytics = relationship("MatchAnalytics", back_populates="match", uselist=False)
    lineups = relationship("Lineup", back_populates="match")


class MatchEvent(Base):
    __tablename__ = "match_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    period: Mapped[MatchPeriod] = mapped_column(Enum(MatchPeriod), nullable=False)
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)  # ms from video start
    game_clock_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=True
    )
    secondary_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
    position_x: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1 normalized
    position_y: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1 normalized
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_auto_detected: Mapped[bool] = mapped_column(default=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    match = relationship("Match", back_populates="events")
