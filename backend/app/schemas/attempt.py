from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.attempt import AttemptStatus
from backend.app.schemas.question import QuestionCandidateOut


class AnswerSubmissionItem(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None


class AttemptSubmitRequest(BaseModel):
    answers: List[AnswerSubmissionItem] = []


class AttemptStartResponse(BaseModel):
    attempt_id: int
    exam_id: int
    exam_title: str
    duration_minutes: int
    started_at: datetime
    expires_at: datetime
    remaining_seconds: int
    questions: List[QuestionCandidateOut]

    model_config = ConfigDict(from_attributes=True)


class AttemptOut(BaseModel):
    id: int
    student_id: int
    exam_id: int
    started_at: datetime
    expires_at: datetime
    submitted_at: Optional[datetime] = None
    status: AttemptStatus

    model_config = ConfigDict(from_attributes=True)
