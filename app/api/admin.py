from datetime import UTC, date, datetime, time, timedelta
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
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
from app.schemas.admin import AlertOut, AuditEventOut, RouteHistoryOut, RoutePointOut, StopOut, VisitComparisonOut
from app.services.audit import write_audit
from app.services.route_analysis import detect_stops, distance_km

router = APIRouter(prefix="/admin", tags=["admin"])


def _day_bounds_utc(selected_day: date) -> tuple[datetime, datetime]:
    """Assumption: all operational timestamps are stored/handled in UTC for cross-branch consistency."""
    start = datetime.combine(selected_day, time.min).replace(tzinfo=UTC)
    end = datetime.combine(selected_day, time.max).replace(tzinfo=UTC)
    return start, end


def _valid_coord(lat: float | None, lng: float | None) -> bool:
    return lat is not None and lng is not None and -90 <= lat <= 90 and -180 <= lng <= 180


async def build_route_history(db: AsyncSession, driver_id: str, selected_day: date) -> RouteHistoryOut:
    day_start, day_end = _day_bounds_utc(selected_day)

    driver = (await db.execute(select(User).where(User.id == driver_id, User.role == Role.driver))).scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    points_raw = (
        await db.execute(
            select(LocationPoint)
            .join(Shift, Shift.id == LocationPoint.shift_id)
            .where(Shift.driver_id == driver_id, LocationPoint.captured_at >= day_start, LocationPoint.captured_at <= day_end)
            .order_by(LocationPoint.captured_at.asc())
        )
    ).scalars().all()

    points = [p for p in points_raw if _valid_coord(p.latitude, p.longitude)]

    visits = (
        await db.execute(
            select(Visit)
            .where(Visit.driver_id == driver_id, Visit.planned_at >= day_start - timedelta(hours=2), Visit.planned_at <= day_end + timedelta(hours=2))
            .order_by(Visit.planned_at.asc())
        )
    ).scalars().all()

    alerts = (
        await db.execute(
            select(Alert)
            .where(Alert.driver_id == driver_id, Alert.created_at >= day_start, Alert.created_at <= day_end)
            .order_by(Alert.created_at.asc())
        )
    ).scalars().all()

    route_actions = [
        "shift_start",
        "shift_end",
        "visit_check_in",
        "visit_check_out",
        "proof_uploaded",
        "alert_generated",
        "location_batch_ingested",
        "route_history_reviewed",
    ]
    actor = User
    audit_rows = (
        await db.execute(
            select(AuditLog, actor.full_name)
            .join(actor, actor.id == AuditLog.actor_user_id, isouter=True)
            .where(
                AuditLog.created_at >= day_start,
                AuditLog.created_at <= day_end,
                AuditLog.action.in_(route_actions),
            )
            .order_by(AuditLog.created_at.asc())
        )
    ).all()

    total_distance = distance_km(points)
    total_duration_minutes = round((points[-1].captured_at - points[0].captured_at).total_seconds() / 60, 2) if len(points) > 1 else 0.0
    average_speed = round((total_distance / (total_duration_minutes / 60)) if total_duration_minutes > 0 else 0.0, 2)

    stops = detect_stops(points, radius_m=50, min_stop_minutes=5)

    visit_items: list[VisitComparisonOut] = []
    delayed_count = 0
    completed_count = 0
    open_count = 0
    for v in visits:
        delay_minutes = 0.0
        if v.actual_arrival_at and v.actual_arrival_at > v.planned_at:
            delay_minutes = round((v.actual_arrival_at - v.planned_at).total_seconds() / 60, 2)

        stay_duration = None
        if v.actual_arrival_at and v.actual_departure_at and v.actual_departure_at > v.actual_arrival_at:
            stay_duration = round((v.actual_departure_at - v.actual_arrival_at).total_seconds() / 60, 2)

        if v.status == VisitStatus.delayed:
            delayed_count += 1
        if v.status == VisitStatus.departed:
            completed_count += 1
        if v.actual_arrival_at and not v.actual_departure_at:
            open_count += 1

        visit_items.append(
            VisitComparisonOut(
                visit_id=v.id,
                customer_name=v.customer_name,
                planned_at=v.planned_at,
                actual_arrival_at=v.actual_arrival_at,
                actual_departure_at=v.actual_departure_at,
                status=v.status.value,
                delay_minutes=delay_minutes,
                stay_duration_minutes=stay_duration,
                latitude=v.planned_latitude,
                longitude=v.planned_longitude,
                driver_note=v.driver_note,
                proof_image_url=v.proof_image_url,
            )
        )

    alert_items = [
        AlertOut(
            id=a.id,
            type=a.type.value,
            severity=getattr(a.severity, "value", str(a.severity)),
            message=a.message,
            created_at=a.created_at,
            status="resolved" if a.is_resolved else "open",
        )
        for a in alerts
    ]

    audit_items = [
        AuditEventOut(
            event_type=row[0].action,
            actor_name=row[1],
            timestamp=row[0].created_at,
            details=row[0].details,
        )
        for row in audit_rows
    ]

    route_deviation_count = len([a for a in alert_items if a.type == AlertType.route_deviation.value])
    total_delay_alerts = len([a for a in alert_items if a.type == AlertType.delay.value])

    return RouteHistoryOut(
        driver_id=driver.id,
        driver_name=driver.full_name,
        date=str(selected_day),
        total_points=len(points),
        started_at=points[0].captured_at if points else None,
        ended_at=points[-1].captured_at if points else None,
        total_distance_km=total_distance,
        total_duration_minutes=total_duration_minutes,
        average_speed_kmh=average_speed,
        total_stops=len(stops),
        route_deviation_count=route_deviation_count,
        total_delay_alerts=total_delay_alerts,
        planned_visits_count=len(visits),
        completed_visits_count=completed_count,
        delayed_visits_count=delayed_count,
        open_visits_count=open_count,
        points=[
            RoutePointOut(
                latitude=p.latitude,
                longitude=p.longitude,
                recorded_at=p.captured_at,
                accuracy=p.accuracy_meters,
                speed=p.speed_kmh,
            )
            for p in points
        ],
        stops=[
            StopOut(
                started_at=s.started_at,
                ended_at=s.ended_at,
                duration_minutes=s.duration_minutes,
                latitude=s.latitude,
                longitude=s.longitude,
                classification=s.classification,
            )
            for s in stops
        ],
        visits=visit_items,
        alerts=alert_items,
        audit_events=audit_items,
    )


@router.get('/drivers')
async def drivers(current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (await db.execute(select(User).where(User.role == Role.driver, User.is_active.is_(True)).order_by(User.full_name))).scalars().all()
    return [{"id": r.id, "name": r.full_name} for r in rows]


@router.get('/drivers/latest-positions')
async def latest_positions(current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> list[dict]:
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


@router.get('/drivers/live')
async def live_driver_map(current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> list[dict]:
    return await latest_positions(current_user=current_user, db=db)


@router.get(
    '/drivers/route-history',
    response_model=RouteHistoryOut,
    summary='Enterprise route review payload by driver/day',
    description='Admin-only endpoint returning normalized route, visits, alerts, stops, metrics, and route-related audit events for operational review.',
)
async def route_history(
    driver_id: str = Query(..., description='Driver UUID'),
    date_value: date = Query(..., alias='date', description='Operational date in YYYY-MM-DD (UTC day boundaries)'),
    current_user: User = Depends(require_roles(Role.admin)),
    db: AsyncSession = Depends(get_db),
) -> RouteHistoryOut:
    payload = await build_route_history(db, driver_id, date_value)
    await write_audit(db, 'route_history_reviewed', 'driver', current_user.id, driver_id, details=str(date_value))
    await db.commit()
    return payload


@router.get('/alerts')
async def alerts(current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)), db: AsyncSession = Depends(get_db)) -> list[dict]:
    records = (await db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(300))).scalars().all()
    return [{"id": a.id, "type": a.type.value, "severity": a.severity.value, "message": a.message, "created_at": a.created_at, "status": "resolved" if a.is_resolved else "open"} for a in records]


@router.get('/audit/route-events')
async def audit_route_events(
    driver_id: str | None = None,
    date_value: date | None = Query(default=None, alias='date'),
    current_user: User = Depends(require_roles(Role.admin)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    start, end = _day_bounds_utc(date_value or datetime.now(UTC).date())
    query = select(AuditLog).where(AuditLog.created_at >= start, AuditLog.created_at <= end)
    if driver_id:
        query = query.where(AuditLog.entity_id == driver_id)
    logs = (await db.execute(query.order_by(AuditLog.created_at.desc()).limit(1000))).scalars().all()
    return [{"event_type": l.action, "timestamp": l.created_at, "details": l.details} for l in logs]


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
