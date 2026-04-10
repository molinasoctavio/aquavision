import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, Enum, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AnnotationType(str, enum.Enum):
    ARROW = "arrow"
    LINE = "line"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    FREEHAND = "freehand"
    TEXT = "text"
    HIGHLIGHT_ZONE = "highlight_zone"
    PLAYER_MARKER = "player_marker"
    TACTICAL_ANIMATION = "tactical_animation"


class Clip(Base):
    __tablename__ = "clips"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_events.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timing
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Follow-cam keyframes: [{time_ms, x, y, zoom}]
    keyframes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    follow_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=True
    )
    follow_ball: Mapped[bool] = mapped_column(Boolean, default=False)

    # Export
    exported_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_exported: Mapped[bool] = mapped_column(default=False)
    export_quality: Mapped[str] = mapped_column(String(20), default="1080p")

    # Sharing
    is_public: Mapped[bool] = mapped_column(default=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)

    # Tags
    is_auto_generated: Mapped[bool] = mapped_column(default=False)
    ability_labels: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    match = relationship("Match", back_populates="clips")
    tags = relationship("ClipTag", back_populates="clip")
    annotations = relationship("Annotation", back_populates="clip")


class ClipTag(Base):
    __tablename__ = "clip_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False
    )
    tag: Mapped[str] = mapped_column(String(100), nullable=False)

    clip = relationship("Clip", back_populates="tags")


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    annotation_type: Mapped[AnnotationType] = mapped_column(
        Enum(AnnotationType), nullable=False
    )
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=3000)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # data schema per type:
    # arrow: {start: {x,y}, end: {x,y}, color, width}
    # line: {points: [{x,y}], color, width}
    # circle: {center: {x,y}, radius, color, fill}
    # rectangle: {topLeft: {x,y}, width, height, color, fill}
    # freehand: {points: [{x,y}], color, width}
    # text: {position: {x,y}, text, fontSize, color}
    # highlight_zone: {points: [{x,y}], color, opacity}
    # player_marker: {position: {x,y}, label, color}
    # tactical_animation: {frames: [{time_offset, elements: [...]}]}

    color: Mapped[str] = mapped_column(String(7), default="#FF0000")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    clip = relationship("Clip", back_populates="annotations")
