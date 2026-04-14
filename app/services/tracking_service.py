from datetime import UTC, datetime, timedelta

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Alert, AlertSeverity, AlertType, LocationPoint, Shift, Visit, VisitStatus
from app.schemas.tracking import LocationIn
from app.services.notifications import publish_notification


async def insert_location_batch(db: AsyncSession, shift_id: str, points: list[LocationIn]) -> int:
    rows = [
        {
            "shift_id": shift_id,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "accuracy_meters": p.accuracy_meters,
            "speed_kmh": p.speed_kmh,
            "captured_at": p.captured_at,
        }
        for p in points
    ]
    await db.execute(insert(LocationPoint), rows)
    return len(rows)


async def generate_alert(
    db: AsyncSession,
    shift: Shift,
    alert_type: AlertType,
    message: str,
    severity: AlertSeverity = AlertSeverity.medium,
) -> None:
    db.add(
        Alert(
            driver_id=shift.driver_id,
            shift_id=shift.id,
            type=alert_type,
            severity=severity,
            message=message,
        )
    )
    await publish_notification(
        db,
        event_type=f"alert.{alert_type.value}",
        title=message,
        severity=severity.value,
        payload={"driver_id": shift.driver_id, "shift_id": shift.id},
    )


async def detect_basic_alerts(db: AsyncSession, shift: Shift) -> None:
    now = datetime.now(UTC)
    overdue_visits = (
        await db.execute(
            select(Visit).where(
                Visit.driver_id == shift.driver_id,
                Visit.status.in_([VisitStatus.planned, VisitStatus.delayed]),
                Visit.planned_at < now - timedelta(minutes=15),
            )
        )
    ).scalars().all()
    for visit in overdue_visits:
        visit.status = VisitStatus.missed
        await generate_alert(
            db,
            shift,
            AlertType.missed_visit,
            f"زيارة فائتة: {visit.customer_name}",
            AlertSeverity.high,
        )
