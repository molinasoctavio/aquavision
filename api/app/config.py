from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AquaVision Analytics"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "https://aquavision.vercel.app"]

    # Auth
    JWT_SECRET_KEY: str = "jwt-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database — Railway injects DATABASE_URL automatically
    DATABASE_URL: str = "postgresql+asyncpg://aquavision:aquavision@localhost:5432/aquavision"
    DATABASE_SYNC_URL: str = "postgresql://aquavision:aquavision@localhost:5432/aquavision"

    # Redis — Railway injects REDIS_URL automatically
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Storage — MinIO (local) or S3-compatible (production)
    S3_ENDPOINT: str = "localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_RAW: str = "aquavision-raw"
    S3_BUCKET_PROCESSED: str = "aquavision-processed"
    S3_BUCKET_CLIPS: str = "aquavision-clips"
    S3_BUCKET_THUMBNAILS: str = "aquavision-thumbnails"
    S3_USE_SSL: bool = False

    # Video Processing
    FFMPEG_PATH: str = "/usr/bin/ffmpeg"
    FFPROBE_PATH: str = "/usr/bin/ffprobe"
    MAX_UPLOAD_SIZE_GB: float = 10.0
    SUPPORTED_VIDEO_FORMATS: list[str] = [
        "mp4", "mov", "avi", "mkv", "webm", "m4v", "flv", "wmv", "ts"
    ]
    VIDEO_PROCESSING_WORKERS: int = 2
    DEFAULT_OUTPUT_FORMAT: str = "mp4"
    DEFAULT_OUTPUT_CODEC: str = "h264"
    HLS_SEGMENT_DURATION: int = 6

    # AI/ML
    YOLO_MODEL_PATH: str = "ml/models/waterpolo_yolo.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.5
    TRACKING_MAX_AGE: int = 30
    TRACKING_MIN_HITS: int = 3
    DETECTION_FRAME_SKIP: int = 3

    # Anthropic Claude
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Live Streaming
    RTMP_SERVER_URL: str = "rtmp://localhost:1935"
    WEBRTC_ENABLED: bool = True

    # CDN
    CDN_BASE_URL: Optional[str] = None

    # Subscriptions (Stripe)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Railway injects DATABASE_URL as postgres:// — fix for asyncpg
        if self.DATABASE_URL.startswith("postgres://"):
            object.__setattr__(
                self, "DATABASE_URL",
                self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1),
            )
        if self.DATABASE_SYNC_URL.startswith("postgres://"):
            object.__setattr__(
                self, "DATABASE_SYNC_URL",
                self.DATABASE_SYNC_URL.replace("postgres://", "postgresql://", 1),
            )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
