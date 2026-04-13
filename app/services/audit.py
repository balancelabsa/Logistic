from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog


async def write_audit(
    db: AsyncSession,
    action: str,
    entity_type: str,
    actor_user_id: str | None,
    entity_id: str | None = None,
    details: str | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
    )
