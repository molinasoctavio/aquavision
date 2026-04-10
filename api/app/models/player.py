import enum
import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Float, Date, ForeignKey, Enum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PlayerPosition(str, enum.Enum):
    GOALKEEPER = "goalkeeper"
    CENTER_FORWARD = "center_forward"  # Boya / Pivot
    CENTER_BACK = "center_back"  # Defensa de boya
    WING = "wing"  # Ala
    FLAT = "flat"  # Lateral
    POINT = "point"  # Base
    UTILITY = "utility"


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cap_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-13
    position: Mapped[PlayerPosition] = mapped_column(
        Enum(PlayerPosition), default=PlayerPosition.UTILITY
    )
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    dominant_hand: Mapped[str] = mapped_column(String(10), default="right")
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_captain: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    team = relationship("Team", back_populates="players")
    stats = relationship("PlayerStats", back_populates="player")
    match_stats = relationship("PlayerMatchStats", back_populates="player")


class PlayerStats(Base):
    """Accumulated career/season stats for a player."""
    __tablename__ = "player_stats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=False
    )
    season_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True
    )
    matches_played: Mapped[int] = mapped_column(Integer, default=0)
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    shots: Mapped[int] = mapped_column(Integer, default=0)
    shots_on_target: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)  # for goalkeepers
    exclusions_drawn: Mapped[int] = mapped_column(Integer, default=0)
    exclusions_committed: Mapped[int] = mapped_column(Integer, default=0)
    steals: Mapped[int] = mapped_column(Integer, default=0)
    turnovers: Mapped[int] = mapped_column(Integer, default=0)
    power_play_goals: Mapped[int] = mapped_column(Integer, default=0)
    penalty_goals: Mapped[int] = mapped_column(Integer, default=0)
    penalty_attempts: Mapped[int] = mapped_column(Integer, default=0)
    minutes_played: Mapped[float] = mapped_column(Float, default=0.0)
    distance_swum_m: Mapped[float] = mapped_column(Float, default=0.0)
    sprint_count: Mapped[int] = mapped_column(Integer, default=0)
    abilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    player = relationship("Player", back_populates="stats")
