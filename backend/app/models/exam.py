import enum
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.question import Question
    from backend.app.models.attempt import ExamAttempt
    from backend.app.models.result import Result


class ExamStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    passing_marks: Mapped[float] = mapped_column(Float, default=40.0, nullable=False)
    status: Mapped[ExamStatus] = mapped_column(Enum(ExamStatus), default=ExamStatus.DRAFT, nullable=False, index=True)
    
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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
    creator: Mapped["User"] = relationship("User", back_populates="created_exams")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="exam", cascade="all, delete-orphan", order_by="Question.order_index")
    attempts: Mapped[List["ExamAttempt"]] = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")
    results: Mapped[List["Result"]] = relationship("Result", back_populates="exam", cascade="all, delete-orphan")
