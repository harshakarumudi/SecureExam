import asyncio
import logging
from sqlalchemy import select
from backend.app.core.database import engine, Base, AsyncSessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models import User, UserRole, AuditLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db() -> None:
    logger.info("Initializing database schema and tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables created successfully.")

    # Seed initial accounts if database is empty
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "admin@secureexam.edu"))
        admin_user = result.scalars().first()
        if not admin_user:
            logger.info("Seeding initial administrator user...")
            admin_user = User(
                email="admin@secureexam.edu",
                hashed_password=get_password_hash("AdminPass123!@#"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(admin_user)

        # Seed initial faculty user
        result = await session.execute(select(User).where(User.email == "faculty@secureexam.edu"))
        faculty_user = result.scalars().first()
        if not faculty_user:
            logger.info("Seeding initial faculty user...")
            faculty_user = User(
                email="faculty@secureexam.edu",
                hashed_password=get_password_hash("FacultyPass123!@#"),
                full_name="Prof. Alan Turing",
                role=UserRole.FACULTY,
                is_active=True
            )
            session.add(faculty_user)

        # Seed initial student user
        result = await session.execute(select(User).where(User.email == "student@secureexam.edu"))
        student_user = result.scalars().first()
        if not student_user:
            logger.info("Seeding initial student user...")
            student_user = User(
                email="student@secureexam.edu",
                hashed_password=get_password_hash("StudentPass123!@#"),
                full_name="Ada Lovelace",
                role=UserRole.STUDENT,
                is_active=True
            )
            session.add(student_user)

        await session.commit()
        logger.info("Database seeding completed.")


if __name__ == "__main__":
    asyncio.run(init_db())
