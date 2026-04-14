from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import Role, Shift, ShiftStatus, User, Visit, VisitStatus
from app.schemas.visit import VisitCheckInOut, VisitCreate, VisitOut
from app.services.audit import write_audit
from app.services.notifications import publish_notification
from app.services.route_analysis import haversine_km
from app.services.tracking_service import generate_alert
from app.models.entities import AlertType, AlertSeverity

router = APIRouter(prefix="/visits", tags=["visits"])
UPLOAD_DIR = Path("uploads/proofs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", response_model=VisitOut)
async def create_visit(
    payload: VisitCreate,
    current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)),
    db: AsyncSession = Depends(get_db),
) -> VisitOut:
    visit = Visit(
        driver_id=payload.driver_id,
        customer_name=payload.customer_name,
        planned_at=payload.planned_at,
        planned_latitude=payload.planned_latitude,
        planned_longitude=payload.planned_longitude,
    )
    db.add(visit)
    await write_audit(db, "visit_created", "visit", current_user.id, visit.id)
    await db.commit()
    return VisitOut.model_validate(visit, from_attributes=True)


@router.get("/mine", response_model=list[VisitOut])
async def my_visits(
    current_user: User = Depends(require_roles(Role.driver)), db: AsyncSession = Depends(get_db)
) -> list[VisitOut]:
    visits = (await db.execute(select(Visit).where(Visit.driver_id == current_user.id).order_by(Visit.planned_at))).scalars().all()
    return [VisitOut.model_validate(v, from_attributes=True) for v in visits]


@router.get("/{visit_id}", response_model=VisitOut)
async def visit_details(
    visit_id: str,
    current_user: User = Depends(require_roles(Role.driver, Role.admin, Role.dispatcher)),
    db: AsyncSession = Depends(get_db),
) -> VisitOut:
    visit = (await db.execute(select(Visit).where(Visit.id == visit_id))).scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return VisitOut.model_validate(visit, from_attributes=True)


@router.post("/{visit_id}/check-in", response_model=VisitOut)
async def check_in(
    visit_id: str,
    payload: VisitCheckInOut,
    current_user: User = Depends(require_roles(Role.driver)),
    db: AsyncSession = Depends(get_db),
) -> VisitOut:
    visit = (await db.execute(select(Visit).where(Visit.id == visit_id, Visit.driver_id == current_user.id))).scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    active_shift = (
        await db.execute(select(Shift).where(Shift.driver_id == current_user.id, Shift.status == ShiftStatus.active))
    ).scalar_one_or_none()
    if not active_shift:
        raise HTTPException(status_code=409, detail="لا يمكن تنفيذ الزيارة بدون وردية نشطة")

    now = datetime.now(UTC)
    visit.actual_arrival_at = now
    visit.check_in_latitude = payload.latitude
    visit.check_in_longitude = payload.longitude
    visit.driver_note = payload.note

    delay_minutes = (now - visit.planned_at).total_seconds() / 60
    if delay_minutes > 15:
        visit.status = VisitStatus.delayed
        await generate_alert(
            db,
            active_shift,
            AlertType.delay,
            f"تأخير زيارة {visit.customer_name} بمقدار {round(delay_minutes)} دقيقة",
            AlertSeverity.medium,
        )
    else:
        visit.status = VisitStatus.arrived

    if visit.planned_latitude and visit.planned_longitude:
        distance_from_plan = haversine_km(
            payload.latitude,
            payload.longitude,
            visit.planned_latitude,
            visit.planned_longitude,
        )
        if distance_from_plan > 1.0:
            await generate_alert(
                db,
                active_shift,
                AlertType.route_deviation,
                f"انحراف عن نقطة الزيارة {visit.customer_name}",
                AlertSeverity.high,
            )

    await write_audit(db, "visit_check_in", "visit", current_user.id, visit.id)
    await db.commit()
    return VisitOut.model_validate(visit, from_attributes=True)


@router.post("/{visit_id}/check-out", response_model=VisitOut)
async def check_out(
    visit_id: str,
    payload: VisitCheckInOut,
    current_user: User = Depends(require_roles(Role.driver)),
    db: AsyncSession = Depends(get_db),
) -> VisitOut:
    visit = (await db.execute(select(Visit).where(Visit.id == visit_id, Visit.driver_id == current_user.id))).scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    visit.status = VisitStatus.departed
    visit.actual_departure_at = datetime.now(UTC)
    visit.check_out_latitude = payload.latitude
    visit.check_out_longitude = payload.longitude
    visit.driver_note = payload.note or visit.driver_note
    await write_audit(db, "visit_check_out", "visit", current_user.id, visit.id)
    await db.commit()
    return VisitOut.model_validate(visit, from_attributes=True)


@router.post("/{visit_id}/proof", response_model=VisitOut)
async def upload_proof(
    visit_id: str,
    file: UploadFile = File(...),
    note: str | None = Form(default=None),
    current_user: User = Depends(require_roles(Role.driver)),
    db: AsyncSession = Depends(get_db),
) -> VisitOut:
    visit = (await db.execute(select(Visit).where(Visit.id == visit_id, Visit.driver_id == current_user.id))).scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    suffix = ".jpg" if file.content_type == "image/jpeg" else ".png"
    filename = f"{visit_id}-{uuid4().hex}{suffix}"
    target = UPLOAD_DIR / filename
    target.write_bytes(content)

    visit.proof_image_url = f"/uploads/proofs/{filename}"
    if note:
        visit.driver_note = note
    await write_audit(db, "proof_uploaded", "visit", current_user.id, visit.id)
    await publish_notification(db, "visit.proof_uploaded", f"تم رفع إثبات للزيارة {visit.customer_name}", payload={"visit_id": visit.id})
    await db.commit()
    return VisitOut.model_validate(visit, from_attributes=True)
