from datetime import datetime

from pydantic import BaseModel, Field


class RoutePointOut(BaseModel):
    latitude: float
    longitude: float
    recorded_at: datetime
    accuracy: float | None = None
    speed: float | None = None


class StopOut(BaseModel):
    started_at: datetime
    ended_at: datetime
    duration_minutes: float
    latitude: float
    longitude: float
    classification: str | None = None


class AlertOut(BaseModel):
    id: str | int
    type: str
    severity: str
    message: str
    created_at: datetime
    status: str = "open"


class VisitComparisonOut(BaseModel):
    visit_id: str
    customer_name: str
    planned_at: datetime
    actual_arrival_at: datetime | None
    actual_departure_at: datetime | None
    status: str
    delay_minutes: float = 0
    stay_duration_minutes: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    driver_note: str | None = None
    proof_image_url: str | None = None


class AuditEventOut(BaseModel):
    event_type: str
    actor_name: str | None = None
    timestamp: datetime
    details: str | None = None


class RouteHistoryOut(BaseModel):
    driver_id: str
    driver_name: str
    date: str
    total_points: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None
    total_distance_km: float = 0
    total_duration_minutes: float = 0
    average_speed_kmh: float = 0
    total_stops: int = 0
    route_deviation_count: int = 0
    total_delay_alerts: int = 0
    planned_visits_count: int = 0
    completed_visits_count: int = 0
    delayed_visits_count: int = 0
    open_visits_count: int = 0
    points: list[RoutePointOut] = Field(default_factory=list)
    stops: list[StopOut] = Field(default_factory=list)
    visits: list[VisitComparisonOut] = Field(default_factory=list)
    alerts: list[AlertOut] = Field(default_factory=list)
    audit_events: list[AuditEventOut] = Field(default_factory=list)
