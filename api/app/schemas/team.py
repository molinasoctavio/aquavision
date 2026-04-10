from pydantic import BaseModel, Field
from datetime import datetime


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    short_name: str = Field(min_length=1, max_length=10)
    logo_url: str | None = None
    primary_color: str = "#0066CC"
    secondary_color: str = "#FFFFFF"
    cap_color: str = "dark"
    city: str | None = None
    country: str | None = None
    division: str | None = None


class TeamResponse(BaseModel):
    id: str
    name: str
    short_name: str
    logo_url: str | None
    primary_color: str
    secondary_color: str
    cap_color: str
    city: str | None
    country: str | None
    division: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamUpdate(BaseModel):
    name: str | None = None
    short_name: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    cap_color: str | None = None
    city: str | None = None
    country: str | None = None
    division: str | None = None
