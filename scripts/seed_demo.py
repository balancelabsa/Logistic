import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import Role, Shift, ShiftStatus, User, Visit


async def seed() -> None:
    async with SessionLocal() as db:
        existing_admin = (await db.execute(select(User).where(User.role == Role.admin))).scalar_one_or_none()
        if not existing_admin:
            admin = User(
                full_name="System Admin",
                phone="900000001",
                password_hash=hash_password("Admin@1234"),
                role=Role.admin,
            )
            db.add(admin)

        driver = (await db.execute(select(User).where(User.phone == "900000101"))).scalar_one_or_none()
        if not driver:
            driver = User(
                full_name="أحمد السائق",
                phone="900000101",
                password_hash=hash_password("Driver@1234"),
                role=Role.driver,
            )
            db.add(driver)
            await db.flush()

            db.add(Shift(driver_id=driver.id, status=ShiftStatus.active, started_at=datetime.now(UTC) - timedelta(hours=1)))
            db.add(
                Visit(
                    driver_id=driver.id,
                    customer_name="متجر النور",
                    planned_at=datetime.now(UTC) + timedelta(hours=1),
                )
            )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
