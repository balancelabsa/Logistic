from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.entities import Role, Shift, ShiftStatus, User

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = (await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*allowed: Role) -> Callable:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return dependency


async def get_active_shift(
    current_user: User = Depends(require_roles(Role.driver)),
    db: AsyncSession = Depends(get_db),
) -> Shift:
    shift = (
        await db.execute(
            select(Shift).where(Shift.driver_id == current_user.id, Shift.status == ShiftStatus.active)
        )
    ).scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=409, detail="No active shift")
    return shift
