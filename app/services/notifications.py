from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import NotificationEvent


async def publish_notification(
    db: AsyncSession,
    event_type: str,
    title: str,
    severity: str = "medium",
    payload: dict | None = None,
) -> None:
    db.add(
        NotificationEvent(
            event_type=event_type,
            title=title,
            severity=severity,
            payload=payload or {},
        )
    )
