from pydantic import BaseModel
from datetime import datetime


class ClipCreate(BaseModel):
    match_id: str
    video_id: str
    title: str
    description: str | None = None
    start_ms: int
    end_ms: int
    follow_player_id: str | None = None
    follow_ball: bool = False
    keyframes: dict | None = None
    ability_labels: list[str] | None = None
    tags: list[str] | None = None


class ClipResponse(BaseModel):
    id: str
    match_id: str
    video_id: str
    title: str
    description: str | None
    start_ms: int
    end_ms: int
    duration_ms: int
    follow_ball: bool
    is_exported: bool
    exported_path: str | None
    thumbnail_path: str | None
    is_public: bool
    share_token: str | None
    is_auto_generated: bool
    ability_labels: list | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnnotationCreate(BaseModel):
    clip_id: str
    annotation_type: str
    timestamp_ms: int
    duration_ms: int = 3000
    data: dict
    color: str = "#FF0000"


class AnnotationResponse(BaseModel):
    id: str
    clip_id: str
    annotation_type: str
    timestamp_ms: int
    duration_ms: int
    data: dict
    color: str
    created_at: datetime

    model_config = {"from_attributes": True}
