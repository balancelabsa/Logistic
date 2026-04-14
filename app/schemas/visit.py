from datetime import datetime

from pydantic import BaseModel, Field

from app.models.entities import VisitStatus


class VisitCreate(BaseModel):
    driver_id: str
    customer_name: str = Field(min_length=2, max_length=120)
    planned_at: datetime
    planned_latitude: float | None = Field(default=None, ge=-90, le=90)
    planned_longitude: float | None = Field(default=None, ge=-180, le=180)


class VisitCheckInOut(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    note: str | None = Field(default=None, max_length=800)


class VisitOut(BaseModel):
    id: str
    driver_id: str
    customer_name: str
    planned_at: datetime
    status: VisitStatus
    actual_arrival_at: datetime | None = None
    actual_departure_at: datetime | None = None
    driver_note: str | None = None
    proof_image_url: str | None = None
