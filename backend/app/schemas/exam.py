from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.exam import ExamStatus
from backend.app.schemas.question import QuestionOut


class ExamBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    duration_minutes: int = Field(..., ge=1, le=360)
    total_marks: float = Field(default=100.0, ge=1.0)
    passing_marks: float = Field(default=40.0, ge=0.0)
    enable_negative_marking: bool = False
    start_time: datetime | None = None
    end_time: datetime | None = None


class ExamCreate(ExamBase):
    pass


class ExamUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    duration_minutes: int | None = Field(None, ge=1, le=360)
    total_marks: float | None = Field(None, ge=1.0)
    passing_marks: float | None = Field(None, ge=0.0)
    enable_negative_marking: bool | None = None
    status: ExamStatus | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class ExamStatusUpdate(BaseModel):
    status: ExamStatus


class ExamOut(ExamBase):
    id: int
    status: ExamStatus
    created_by: int
    created_at: datetime
    updated_at: datetime
    question_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ExamDetailOut(ExamOut):
    questions: list[QuestionOut] = []

    model_config = ConfigDict(from_attributes=True)


class ExamCandidateOut(ExamBase):
    id: int
    status: ExamStatus
    question_count: int = 0

    model_config = ConfigDict(from_attributes=True)
