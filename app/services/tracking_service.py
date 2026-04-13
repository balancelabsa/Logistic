from datetime import timedelta

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Alert, AlertType, LocationPoint, Shift, Visit, VisitStatus
from app.schemas.tracking import LocationIn


async def insert_location_batch(db: AsyncSession, shift_id: str, points: list[LocationIn]) -> int:
    rows = [
        {
            "shift_id": shift_id,
            "latitude": point.latitude,
            "longitude": point.longitude,
            "speed_kmh": point.speed_kmh,
            "captured_at": point.captured_at,
        }
        for point in points
    ]
    await db.execute(insert(LocationPoint), rows)
    return len(rows)


async def detect_basic_alerts(db: AsyncSession, shift: Shift) -> list[Alert]:
    alerts: list[Alert] = []
    missed_visits = (
        await db.execute(
            select(Visit).where(
                Visit.driver_id == shift.driver_id,
                Visit.status == VisitStatus.pending,
                Visit.planned_at < (shift.started_at + timedelta(hours=8)),
            )
        )
    ).scalars().all()
    for visit in missed_visits:
        alerts.append(
            Alert(
                driver_id=shift.driver_id,
                shift_id=shift.id,
                type=AlertType.missed_visit,
                message=f"Missed visit: {visit.customer_name}",
            )
        )
    for alert in alerts:
        db.add(alert)
    return alerts
