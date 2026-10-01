from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.app.models.attempt import AttemptStatus
from backend.app.schemas.question import QuestionCandidateOut


class AnswerSubmissionItem(BaseModel):
    question_id: int
    selected_option_id: int | None = None


class AttemptSubmitRequest(BaseModel):
    answers: list[AnswerSubmissionItem] = []


class SavedAnswerItem(BaseModel):
    question_id: int
    selected_option_id: int | None = None
    is_marked_for_review: bool = False

    model_config = ConfigDict(from_attributes=True)


class AnswerAutoSaveRequest(BaseModel):
    question_id: int
    selected_option_id: int | None = None
    is_marked_for_review: bool = False


class AnswerAutoSaveResponse(BaseModel):
    status: str = "saved"
    question_id: int
    selected_option_id: int | None = None
    is_marked_for_review: bool = False
    recorded_at: datetime


class ExamViolationRequest(BaseModel):
    event_type: str  # TAB_SWITCH, FULLSCREEN_EXIT, WINDOW_BLUR, WINDOW_FOCUS
    details: str | None = None


class ExamViolationResponse(BaseModel):
    violation_count: int
    warning_level: int
    message: str
    is_terminated: bool
    termination_reason: str | None = None
    timestamp: datetime


class AttemptStatusResponse(BaseModel):
    attempt_id: int
    status: AttemptStatus
    remaining_seconds: int
    violation_count: int
    is_terminated: bool
    termination_reason: str | None = None
    expires_at: datetime


class AttemptStartResponse(BaseModel):
    attempt_id: int
    exam_id: int
    exam_title: str
    duration_minutes: int
    total_marks: float = 100.0
    enable_negative_marking: bool = False
    started_at: datetime
    expires_at: datetime
    remaining_seconds: int
    violation_count: int = 0
    status: AttemptStatus
    questions: list[QuestionCandidateOut]
    saved_answers: list[SavedAnswerItem] = []

    model_config = ConfigDict(from_attributes=True)


class AttemptOut(BaseModel):
    id: int
    student_id: int
    exam_id: int
    started_at: datetime
    expires_at: datetime
    submitted_at: datetime | None = None
    terminated_at: datetime | None = None
    termination_reason: str | None = None
    violation_count: int = 0
    status: AttemptStatus

    model_config = ConfigDict(from_attributes=True)


class ExamViolationOut(BaseModel):
    id: int
    attempt_id: int
    student_id: int
    student_name: str | None = None
    event_type: str
    warning_number: int | None = None
    details: str | None = None
    ip_address: str | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ExamAttemptMonitorOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    student_email: str
    status: AttemptStatus
    started_at: datetime
    submitted_at: datetime | None = None
    terminated_at: datetime | None = None
    termination_reason: str | None = None
    violation_count: int
    score: float | None = None
    max_score: float | None = None
    percentage: float | None = None
    passed: bool | None = None

    model_config = ConfigDict(from_attributes=True)
