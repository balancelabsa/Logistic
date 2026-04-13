from datetime import datetime

from pydantic import BaseModel, Field

from app.models.entities import ShiftStatus


class ShiftResponse(BaseModel):
    shift_id: str
    status: ShiftStatus
    started_at: datetime
    ended_at: datetime | None = None


class LocationIn(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed_kmh: float | None = Field(default=None, ge=0)
    captured_at: datetime


class BulkLocationIn(BaseModel):
    points: list[LocationIn] = Field(min_length=1, max_length=500)
