from datetime import UTC, date, datetime, time
from io import BytesIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import (
    Alert,
    AlertType,
    AuditLog,
    LocationPoint,
    NotificationEvent,
    Role,
    Shift,
    User,
    Visit,
    VisitStatus,
)
from app.schemas.admin import AlertOut, RouteHistoryOut, RoutePointOut, StopOut, VisitComparisonOut
from app.services.audit import write_audit
from app.services.route_analysis import detect_stops, distance_km

router = APIRouter(prefix="/admin", tags=["admin"])


async def build_route_history(db: AsyncSession, driver_id: str, date_value: date) -> RouteHistoryOut:
    day_start = datetime.combine(date_value, time.min).replace(tzinfo=UTC)
    day_end = datetime.combine(date_value, time.max).replace(tzinfo=UTC)
    driver = (await db.execute(select(User).where(User.id == driver_id))).scalar_one()
    points = (
        await db.execute(
            select(LocationPoint)
            .join(Shift, Shift.id == LocationPoint.shift_id)
            .where(Shift.driver_id == driver_id, LocationPoint.captured_at.between(day_start, day_end))
            .order_by(LocationPoint.captured_at)
        )
    ).scalars().all()
    visits = (
        await db.execute(select(Visit).where(Visit.driver_id == driver_id, Visit.planned_at.between(day_start, day_end)).order_by(Visit.planned_at))
    ).scalars().all()
    alerts = (
        await db.execute(select(Alert).where(Alert.driver_id == driver_id, Alert.created_at.between(day_start, day_end)).order_by(Alert.created_at))
    ).scalars().all()

    total_distance = distance_km(points)
    total_minutes = (points[-1].captured_at - points[0].captured_at).total_seconds() / 60 if len(points) > 1 else 0.0
    avg_speed = round((total_distance / (total_minutes / 60)) if total_minutes > 0 else 0, 2)
    stops = detect_stops(points)

    return RouteHistoryOut(
        driver_id=driver_id,
        driver_name=driver.full_name,
        date=str(date_value),
        total_points=len(points),
        started_at=points[0].captured_at if points else None,
        ended_at=points[-1].captured_at if points else None,
        total_distance_km=total_distance,
        total_duration_minutes=round(total_minutes, 2),
        average_speed_kmh=avg_speed,
        total_stops=len(stops),
        route_deviation_count=len([a for a in alerts if a.type == AlertType.route_deviation]),
        total_delay_alerts=len([a for a in alerts if a.type == AlertType.delay]),
        points=[RoutePointOut(latitude=p.latitude, longitude=p.longitude, recorded_at=p.captured_at) for p in points],
        stops=[StopOut(**s.__dict__) for s in stops],
        visits=[
            VisitComparisonOut(
                visit_id=v.id,
                customer_name=v.customer_name,
                planned_at=v.planned_at,
                actual_arrival_at=v.actual_arrival_at,
                actual_departure_at=v.actual_departure_at,
                status=v.status.value,
                delay_minutes=round((v.actual_arrival_at - v.planned_at).total_seconds() / 60, 2) if v.actual_arrival_at and v.actual_arrival_at > v.planned_at else 0,
                latitude=v.planned_latitude,
                longitude=v.planned_longitude,
                driver_note=v.driver_note,
                proof_image_url=v.proof_image_url,
            )
            for v in visits
        ],
        alerts=[AlertOut(type=a.type.value, severity=a.severity.value, message=a.message, created_at=a.created_at) for a in alerts],
    )


@router.get('/drivers')
async def drivers(current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (await db.execute(select(User).where(User.role == Role.driver, User.is_active.is_(True)).order_by(User.full_name))).scalars().all()
    return [{"id": r.id, "name": r.full_name} for r in rows]


@router.get('/drivers/live')
async def live_driver_map(current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> list[dict]:
    stmt = (
        select(User.id, User.full_name, LocationPoint.latitude, LocationPoint.longitude, LocationPoint.captured_at)
        .join(Shift, Shift.driver_id == User.id)
        .join(LocationPoint, LocationPoint.shift_id == Shift.id)
        .where(Shift.status == 'active')
        .order_by(LocationPoint.captured_at.desc())
        .limit(500)
    )
    rows = (await db.execute(stmt)).all()
    return [{"driver_id": r.id, "driver_name": r.full_name, "lat": r.latitude, "lng": r.longitude, "captured_at": r.captured_at} for r in rows]


@router.get('/drivers/route-history', response_model=RouteHistoryOut)
async def route_history(driver_id: str = Query(...), date_value: date = Query(..., alias='date'), current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> RouteHistoryOut:
    payload = await build_route_history(db, driver_id, date_value)
    await write_audit(db, 'route_history_reviewed', 'driver', current_user.id, driver_id, details=str(date_value))
    await db.commit()
    return payload


@router.get('/alerts')
async def alerts(current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> list[dict]:
    records = (await db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(300))).scalars().all()
    return [{"id": a.id, "type": a.type.value, "severity": a.severity.value, "message": a.message, "created_at": a.created_at} for a in records]


@router.get('/audit-trail')
async def audit_trail(current_user: User = Depends(require_roles(Role.admin)), db: AsyncSession = Depends(get_db)) -> list[dict]:
    logs = (await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1000))).scalars().all()
    return [{"id": l.id, "action": l.action, "entity_type": l.entity_type, "entity_id": l.entity_id, "created_at": l.created_at} for l in logs]


@router.get('/notifications')
async def notifications(since_id: int = 0, current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> dict:
    records = (await db.execute(select(NotificationEvent).where(NotificationEvent.id > since_id).order_by(NotificationEvent.id))).scalars().all()
    return {"unread": len(records), "items": [{"id": n.id, "event_type": n.event_type, "severity": n.severity, "title": n.title, "payload": n.payload, "created_at": n.created_at} for n in records]}


@router.get('/reports/overview')
async def reports_overview(current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> dict:
    drivers = await db.scalar(select(func.count()).select_from(User).where(User.role == Role.driver))
    active_drivers = await db.scalar(select(func.count()).select_from(Shift).where(Shift.status == 'active'))
    delayed_visits = await db.scalar(select(func.count()).select_from(Visit).where(Visit.status == VisitStatus.delayed))
    missed_visits = await db.scalar(select(func.count()).select_from(Visit).where(Visit.status == VisitStatus.missed))
    open_alerts = await db.scalar(select(func.count()).select_from(Alert).where(Alert.is_resolved.is_(False)))
    long_stops = await db.scalar(select(func.count()).select_from(Alert).where(Alert.type == AlertType.long_stop))
    return {"drivers": drivers, "active_drivers": active_drivers, "active_shifts": active_drivers, "delayed_visits": delayed_visits, "missed_visits": missed_visits, "open_alerts": open_alerts, "long_stops": long_stops}


@router.get('/reports/route-pdf')
async def route_report_pdf(driver_id: str, date_value: date = Query(..., alias='date'), current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    report = await build_route_history(db, driver_id, date_value)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.drawString(50, 800, f'Driver: {report.driver_name}')
    pdf.drawString(50, 780, f'Date: {report.date}')
    pdf.drawString(50, 760, f'Distance(km): {report.total_distance_km}')
    pdf.drawString(50, 740, f'Duration(min): {report.total_duration_minutes}')
    pdf.drawString(50, 720, f'Stops: {report.total_stops}')
    pdf.drawString(50, 700, f'Alerts: {len(report.alerts)}')
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type='application/pdf', headers={'Content-Disposition': 'inline; filename=route-report.pdf'})
