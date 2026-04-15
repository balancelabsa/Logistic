import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import Role, User


DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"


async def init_admin() -> None:
    async with SessionLocal() as db:
        existing = (
            await db.execute(
                select(User).where(
                    User.role == Role.admin,
                    User.phone == DEFAULT_USERNAME,
                )
            )
        ).scalar_one_or_none()

        if existing:
            print("Admin user already exists")
            return

        admin = User(
            full_name="admin",
            phone=DEFAULT_USERNAME,
            password_hash=hash_password(DEFAULT_PASSWORD),
            role=Role.admin,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print("Admin user created")
        print(f"username:{DEFAULT_USERNAME}")
        print(f"password:{DEFAULT_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(init_admin())
