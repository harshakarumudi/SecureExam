from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.exam import ExamStatus
from backend.app.schemas.question import QuestionOut, QuestionCandidateOut


class ExamBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(..., ge=1, le=360)
    total_marks: float = Field(default=100.0, ge=1.0)
    passing_marks: float = Field(default=40.0, ge=0.0)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ExamCreate(ExamBase):
    pass


class ExamUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=360)
    total_marks: Optional[float] = Field(None, ge=1.0)
    passing_marks: Optional[float] = Field(None, ge=0.0)
    status: Optional[ExamStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


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
    questions: List[QuestionOut] = []

    model_config = ConfigDict(from_attributes=True)


class ExamCandidateOut(ExamBase):
    id: int
    status: ExamStatus
    question_count: int = 0

    model_config = ConfigDict(from_attributes=True)
