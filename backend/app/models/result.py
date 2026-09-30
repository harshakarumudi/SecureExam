from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.attempt import ExamAttempt
    from backend.app.models.user import User
    from backend.app.models.exam import Exam


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    attempt_id: Mapped[int] = mapped_column(Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_id: Mapped[int] = mapped_column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="result")
    student: Mapped["User"] = relationship("User", back_populates="results")
    exam: Mapped["Exam"] = relationship("Exam", back_populates="results")
