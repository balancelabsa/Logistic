from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import Role, User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate
from app.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(Role.admin, Role.dispatcher)),
) -> dict:
    existing = (await db.execute(select(User).where(User.phone == payload.phone))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Phone already exists")
    user = User(
        full_name=payload.full_name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await write_audit(db, "user_created", "user", actor.id, user.id, f"Role={payload.role.value}")
    await db.commit()
    return {"message": "User created", "user_id": user.id}


@router.post("/bootstrap-admin", status_code=status.HTTP_201_CREATED)
async def bootstrap_admin(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> dict:
    admins_count = (await db.execute(select(User).where(User.role == Role.admin))).scalars().first()
    if admins_count:
        raise HTTPException(status_code=409, detail="Admin already exists")
    admin = User(
        full_name=payload.full_name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=Role.admin,
    )
    db.add(admin)
    await write_audit(db, "bootstrap_admin", "user", admin.id, admin.id)
    await db.commit()
    return {"message": "Admin bootstrapped", "user_id": admin.id}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = (await db.execute(select(User).where(User.phone == payload.phone, User.is_active.is_(True)))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token, expires = create_access_token(user.id, user.role)
    await write_audit(db, "login", "user", user.id, user.id)
    await db.commit()
    return TokenResponse(access_token=token, expires_at=expires, user_id=user.id, role=user.role)


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "role": current_user.role,
    }
