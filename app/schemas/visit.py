from datetime import datetime

from pydantic import BaseModel, Field

from app.models.entities import VisitStatus


class VisitCreate(BaseModel):
    driver_id: str
    customer_name: str = Field(min_length=2, max_length=120)
    planned_at: datetime


class VisitCheckInOut(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    notes: str | None = Field(default=None, max_length=800)


class VisitOut(BaseModel):
    id: str
    driver_id: str
    customer_name: str
    planned_at: datetime
    status: VisitStatus
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    notes: str | None = None
