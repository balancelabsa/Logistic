from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import Role, User, Visit, VisitStatus
from app.schemas.visit import VisitCheckInOut, VisitCreate, VisitOut
from app.services.audit import write_audit

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=VisitOut)
async def create_visit(
    payload: VisitCreate,
    current_user: User = Depends(require_roles(Role.admin, Role.dispatcher)),
    db: AsyncSession = Depends(get_db),
) -> VisitOut:
    visit = Visit(driver_id=payload.driver_id, customer_name=payload.customer_name, planned_at=payload.planned_at)
    db.add(visit)
    await write_audit(db, "visit_created", "visit", current_user.id, visit.id)
    await db.commit()
    return VisitOut.model_validate(visit, from_attributes=True)


@router.get("/mine", response_model=list[VisitOut])
async def my_visits(
    current_user: User = Depends(require_roles(Role.driver)), db: AsyncSession = Depends(get_db)
) -> list[VisitOut]:
    visits = (await db.execute(select(Visit).where(Visit.driver_id == current_user.id))).scalars().all()
    return [VisitOut.model_validate(v, from_attributes=True) for v in visits]


@router.post("/{visit_id}/check-in", response_model=VisitOut)
async def check_in(
    visit_id: str,
    payload: VisitCheckInOut,
    current_user: User = Depends(require_roles(Role.driver)),
    db: AsyncSession = Depends(get_db),
) -> VisitOut:
    visit = (
        await db.execute(select(Visit).where(Visit.id == visit_id, Visit.driver_id == current_user.id))
    ).scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    visit.status = VisitStatus.checked_in
    visit.check_in_at = datetime.now(UTC)
    visit.check_in_latitude = payload.latitude
    visit.check_in_longitude = payload.longitude
    visit.notes = payload.notes
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
    visit = (
        await db.execute(select(Visit).where(Visit.id == visit_id, Visit.driver_id == current_user.id))
    ).scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    visit.status = VisitStatus.checked_out
    visit.check_out_at = datetime.now(UTC)
    visit.check_out_latitude = payload.latitude
    visit.check_out_longitude = payload.longitude
    visit.notes = payload.notes
    await write_audit(db, "visit_check_out", "visit", current_user.id, visit.id)
    await db.commit()
    return VisitOut.model_validate(visit, from_attributes=True)
