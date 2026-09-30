import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.api.deps import get_db
from backend.app.core.database import Base
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User, UserRole
from backend.main import app

# Use isolated test SQLite database
TEST_DB_URL = "sqlite+aiosqlite:///./test_secureexam.db"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed baseline users
    async with TestSessionLocal() as db:
        admin = User(
            email="admin@test.edu",
            full_name="Admin User",
            hashed_password=get_password_hash("Admin@123456"),
            role=UserRole.ADMIN,
            is_active=True
        )
        faculty1 = User(
            email="faculty1@test.edu",
            full_name="Faculty One",
            hashed_password=get_password_hash("Faculty@123456"),
            role=UserRole.FACULTY,
            is_active=True
        )
        faculty2 = User(
            email="faculty2@test.edu",
            full_name="Faculty Two",
            hashed_password=get_password_hash("Faculty@123456"),
            role=UserRole.FACULTY,
            is_active=True
        )
        student1 = User(
            email="student1@test.edu",
            full_name="Student One",
            hashed_password=get_password_hash("Student@123456"),
            role=UserRole.STUDENT,
            is_active=True
        )
        student2 = User(
            email="student2@test.edu",
            full_name="Student Two",
            hashed_password=get_password_hash("Student@123456"),
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add_all([admin, faculty1, faculty2, student1, student2])
        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

def make_auth_headers(email: str, role: str, user_id: int):
    token = create_access_token(subject=str(user_id), role=role)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers():
    return make_auth_headers("admin@test.edu", "ADMIN", 1)

@pytest.fixture
def faculty1_headers():
    return make_auth_headers("faculty1@test.edu", "FACULTY", 2)

@pytest.fixture
def faculty2_headers():
    return make_auth_headers("faculty2@test.edu", "FACULTY", 3)

@pytest.fixture
def student1_headers():
    return make_auth_headers("student1@test.edu", "STUDENT", 4)

@pytest.fixture
def student2_headers():
    return make_auth_headers("student2@test.edu", "STUDENT", 5)
