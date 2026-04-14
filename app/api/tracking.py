from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_active_shift, require_roles
from app.db.session import get_db
from app.models.entities import AlertSeverity, AlertType, LocationPoint, Role, Shift, ShiftStatus, User
from app.schemas.tracking import BulkLocationIn, ShiftResponse
from app.services.audit import write_audit
from app.services.route_analysis import haversine_km
from app.services.tracking_service import detect_basic_alerts, generate_alert, insert_location_batch

router = APIRouter(prefix="/shifts", tags=["shifts"])


@router.post("/start", response_model=ShiftResponse)
async def start_shift(
    current_user: User = Depends(require_roles(Role.driver)),
    db: AsyncSession = Depends(get_db),
) -> ShiftResponse:
    active = (await db.execute(select(Shift).where(Shift.driver_id == current_user.id, Shift.status == ShiftStatus.active))).scalar_one_or_none()
    if active:
        raise HTTPException(status_code=409, detail="Active shift already exists")
    shift = Shift(driver_id=current_user.id, status=ShiftStatus.active)
    db.add(shift)
    await write_audit(db, "shift_start", "shift", current_user.id, shift.id)
    await db.commit()
    return ShiftResponse(shift_id=shift.id, status=shift.status, started_at=shift.started_at)


@router.post("/{shift_id}/end", response_model=ShiftResponse)
async def end_shift(
    shift_id: str,
    current_user: User = Depends(require_roles(Role.driver)),
    db: AsyncSession = Depends(get_db),
) -> ShiftResponse:
    shift = (
        await db.execute(
            select(Shift).where(Shift.id == shift_id, Shift.driver_id == current_user.id, Shift.status == ShiftStatus.active)
        )
    ).scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    shift.status = ShiftStatus.ended
    shift.ended_at = datetime.now(UTC)
    await detect_basic_alerts(db, shift)
    await write_audit(db, "shift_end", "shift", current_user.id, shift.id)
    await db.commit()
    return ShiftResponse(shift_id=shift.id, status=shift.status, started_at=shift.started_at, ended_at=shift.ended_at)


@router.post("/active/locations")
async def ingest_locations(
    payload: BulkLocationIn,
    active_shift: Shift = Depends(get_active_shift),
    current_user: User = Depends(require_roles(Role.driver)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    inserted = await insert_location_batch(db, active_shift.id, payload.points)

    latest = (
        await db.execute(
            select(LocationPoint).where(LocationPoint.shift_id == active_shift.id).order_by(LocationPoint.captured_at.desc()).limit(2)
        )
    ).scalars().all()
    if len(latest) == 2:
        moved_km = haversine_km(latest[0].latitude, latest[0].longitude, latest[1].latitude, latest[1].longitude)
        minutes = abs((latest[0].captured_at - latest[1].captured_at).total_seconds()) / 60
        if moved_km < 0.03 and minutes >= 5:
            await generate_alert(
                db,
                active_shift,
                AlertType.long_stop,
                "توقف طويل أثناء الوردية",
                AlertSeverity.medium,
            )

        if moved_km > 2 and minutes <= 2:
            await generate_alert(
                db,
                active_shift,
                AlertType.route_deviation,
                "انحراف مفاجئ عن المسار المتوقع",
                AlertSeverity.high,
            )

    await write_audit(db, "location_batch_ingested", "shift", current_user.id, active_shift.id, details=f"count={inserted}")
    await db.commit()
    return {"inserted": inserted, "shift_id": active_shift.id}


@router.get("/my-summary")
async def my_shift_summary(
    current_user: User = Depends(require_roles(Role.driver)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    shifts = (
        await db.execute(select(Shift).where(Shift.driver_id == current_user.id, Shift.started_at >= today_start))
    ).scalars().all()
    total_minutes = 0
    for shift in shifts:
        end_time = shift.ended_at or datetime.now(UTC)
        total_minutes += int((end_time - shift.started_at).total_seconds() / 60)
    return {"today_shifts": len(shifts), "total_minutes": total_minutes}
