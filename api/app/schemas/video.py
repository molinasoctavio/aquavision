from pydantic import BaseModel, Field
from datetime import datetime


class VideoUploadResponse(BaseModel):
    id: str
    title: str
    status: str
    upload_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VideoResponse(BaseModel):
    id: str
    match_id: str | None
    title: str
    description: str | None
    source: str
    status: str
    original_filename: str | None
    file_size_bytes: int | None
    duration_seconds: float | None
    width: int | None
    height: int | None
    fps: float | None
    hls_path: str | None
    thumbnail_path: str | None
    is_stabilized: bool
    is_panoramic: bool
    processing_progress: float
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class VideoURLIngest(BaseModel):
    url: str
    title: str | None = None
    match_id: str | None = None


class VideoProcessingStatus(BaseModel):
    video_id: str
    status: str
    progress: float
    current_step: str | None = None
    error: str | None = None
