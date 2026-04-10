import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, Enum, BigInteger, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class VideoStatus(str, enum.Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    QUEUED = "queued"
    TRANSCODING = "transcoding"
    STABILIZING = "stabilizing"
    ANALYZING = "analyzing"
    GENERATING_HLS = "generating_hls"
    READY = "ready"
    ERROR = "error"


class VideoSource(str, enum.Enum):
    UPLOAD = "upload"
    URL = "url"
    RTMP = "rtmp"
    RTSP = "rtsp"
    WEBRTC = "webrtc"
    IP_CAMERA = "ip_camera"
    MOBILE_APP = "mobile_app"
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    YOUTUBE = "youtube"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id"), nullable=True
    )
    camera_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source: Mapped[VideoSource] = mapped_column(
        Enum(VideoSource), default=VideoSource.UPLOAD
    )
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[VideoStatus] = mapped_column(
        Enum(VideoStatus), default=VideoStatus.UPLOADING
    )

    # File info
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    hls_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Video metadata
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    codec: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bitrate: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Processing
    is_stabilized: Mapped[bool] = mapped_column(default=False)
    is_panoramic: Mapped[bool] = mapped_column(default=False)
    camera_angle: Mapped[str | None] = mapped_column(String(50), nullable=True)
    processing_progress: Mapped[float] = mapped_column(Float, default=0.0)
    processing_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    processing_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    match = relationship("Match", back_populates="videos")


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    camera_type: Mapped[str] = mapped_column(String(50), nullable=False)  # fixed, mobile, drone
    stream_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)  # overhead, sideline, goal
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
