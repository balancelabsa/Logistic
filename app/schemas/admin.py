from datetime import datetime

from pydantic import BaseModel


class RoutePointOut(BaseModel):
    latitude: float
    longitude: float
    recorded_at: datetime


class StopOut(BaseModel):
    started_at: datetime
    ended_at: datetime
    duration_minutes: float
    latitude: float
    longitude: float


class AlertOut(BaseModel):
    type: str
    severity: str
    message: str
    created_at: datetime


class VisitComparisonOut(BaseModel):
    visit_id: str
    customer_name: str
    planned_at: datetime
    actual_arrival_at: datetime | None
    actual_departure_at: datetime | None
    status: str
    delay_minutes: float
    latitude: float | None
    longitude: float | None
    driver_note: str | None
    proof_image_url: str | None


class RouteHistoryOut(BaseModel):
    driver_id: str
    driver_name: str
    date: str
    total_points: int
    started_at: datetime | None
    ended_at: datetime | None
    total_distance_km: float
    total_duration_minutes: float
    average_speed_kmh: float
    total_stops: int
    route_deviation_count: int
    total_delay_alerts: int
    points: list[RoutePointOut]
    stops: list[StopOut]
    visits: list[VisitComparisonOut]
    alerts: list[AlertOut]
