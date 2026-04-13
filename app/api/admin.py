from datetime import date, datetime, time

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import Alert, AuditLog, LocationPoint, Role, Shift, User, Visit, VisitStatus

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/drivers/live")
async def live_driver_map(
    current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = (
        select(User.id, User.full_name, LocationPoint.latitude, LocationPoint.longitude, LocationPoint.captured_at)
        .join(Shift, Shift.driver_id == User.id)
        .join(LocationPoint, LocationPoint.shift_id == Shift.id)
        .where(Shift.status == "active")
        .order_by(LocationPoint.captured_at.desc())
        .limit(200)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "driver_id": r.id,
            "driver_name": r.full_name,
            "lat": r.latitude,
            "lng": r.longitude,
            "captured_at": r.captured_at,
        }
        for r in rows
    ]


@router.get("/route-history/{driver_id}")
async def route_history(
    driver_id: str,
    day: date,
    current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    start_dt = datetime.combine(day, time.min)
    end_dt = datetime.combine(day, time.max)
    points = (
        await db.execute(
            select(LocationPoint)
            .join(Shift, Shift.id == LocationPoint.shift_id)
            .where(Shift.driver_id == driver_id, LocationPoint.captured_at.between(start_dt, end_dt))
            .order_by(LocationPoint.captured_at)
        )
    ).scalars().all()
    return {
        "driver_id": driver_id,
        "day": str(day),
        "points": [
            {
                "lat": p.latitude,
                "lng": p.longitude,
                "speed_kmh": p.speed_kmh,
                "captured_at": p.captured_at,
            }
            for p in points
        ],
    }


@router.get("/alerts")
async def alerts(
    current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    records = (await db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(300))).scalars().all()
    return [
        {
            "id": a.id,
            "driver_id": a.driver_id,
            "type": a.type,
            "message": a.message,
            "is_resolved": a.is_resolved,
            "created_at": a.created_at,
        }
        for a in records
    ]


@router.get("/audit-trail")
async def audit_trail(
    current_user: User = Depends(require_roles(Role.admin)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    logs = (await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1000))).scalars().all()
    return [
        {
            "id": log.id,
            "actor_user_id": log.actor_user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.get("/reports/overview")
async def reports_overview(
    current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    drivers = await db.scalar(select(func.count()).select_from(User).where(User.role == Role.driver))
    active_shifts = await db.scalar(select(func.count()).select_from(Shift).where(Shift.status == "active"))
    visits_done = await db.scalar(select(func.count()).select_from(Visit).where(Visit.status == VisitStatus.checked_out))
    visits_missed = await db.scalar(select(func.count()).select_from(Visit).where(Visit.status == VisitStatus.missed))
    total_alerts = await db.scalar(select(func.count()).select_from(Alert))
    return {
        "drivers": drivers,
        "active_shifts": active_shifts,
        "visits_done": visits_done,
        "visits_missed": visits_missed,
        "total_alerts": total_alerts,
    }
