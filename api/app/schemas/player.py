from pydantic import BaseModel, Field
from datetime import date, datetime


class PlayerCreate(BaseModel):
    team_id: str
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    cap_number: int = Field(ge=1, le=13)
    position: str = "utility"
    date_of_birth: date | None = None
    height_cm: int | None = None
    weight_kg: float | None = None
    dominant_hand: str = "right"
    nationality: str | None = None
    photo_url: str | None = None


class PlayerResponse(BaseModel):
    id: str
    team_id: str
    first_name: str
    last_name: str
    cap_number: int
    position: str
    date_of_birth: date | None
    height_cm: int | None
    weight_kg: float | None
    dominant_hand: str
    nationality: str | None
    photo_url: str | None
    is_active: bool
    is_captain: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PlayerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    cap_number: int | None = None
    position: str | None = None
    date_of_birth: date | None = None
    height_cm: int | None = None
    weight_kg: float | None = None
    dominant_hand: str | None = None
    nationality: str | None = None
    photo_url: str | None = None
    is_active: bool | None = None
    is_captain: bool | None = None


class PlayerProfileResponse(BaseModel):
    player: PlayerResponse
    career_stats: dict | None = None
    recent_matches: list[dict] | None = None
    highlight_clips: list[dict] | None = None
    ability_ratings: dict | None = None
