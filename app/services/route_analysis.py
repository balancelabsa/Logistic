from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt

from app.models.entities import LocationPoint


@dataclass
class StopWindow:
    started_at: datetime
    ended_at: datetime
    duration_minutes: float
    latitude: float
    longitude: float


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * r * asin(sqrt(a))


def distance_km(points: list[LocationPoint]) -> float:
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(points)):
        p1, p2 = points[i - 1], points[i]
        total += haversine_km(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
    return round(total, 3)


def detect_stops(points: list[LocationPoint], radius_m: float = 50, min_stop_minutes: int = 5) -> list[StopWindow]:
    if len(points) < 2:
        return []
    stops: list[StopWindow] = []
    start_idx = 0
    for idx in range(1, len(points)):
        segment_m = haversine_km(
            points[start_idx].latitude,
            points[start_idx].longitude,
            points[idx].latitude,
            points[idx].longitude,
        ) * 1000
        if segment_m > radius_m:
            start_idx = idx
            continue
        elapsed = (points[idx].captured_at - points[start_idx].captured_at).total_seconds() / 60
        if elapsed >= min_stop_minutes:
            stops.append(
                StopWindow(
                    started_at=points[start_idx].captured_at,
                    ended_at=points[idx].captured_at,
                    duration_minutes=round(elapsed, 2),
                    latitude=points[start_idx].latitude,
                    longitude=points[start_idx].longitude,
                )
            )
            start_idx = idx + 1
            if start_idx >= len(points):
                break
    return stops
