import enum
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.exam import Exam
    from backend.app.models.attempt import ExamAttempt
    from backend.app.models.result import Result


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    created_exams: Mapped[List["Exam"]] = relationship("Exam", back_populates="creator", cascade="all, delete-orphan")
    attempts: Mapped[List["ExamAttempt"]] = relationship("ExamAttempt", back_populates="student", cascade="all, delete-orphan")
    results: Mapped[List["Result"]] = relationship("Result", back_populates="student", cascade="all, delete-orphan")
