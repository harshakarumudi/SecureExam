from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ResultOut(BaseModel):
    id: int
    attempt_id: int
    student_id: int
    exam_id: int
    total_score: float
    max_score: float
    percentage: float
    passed: bool
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResultDetailOut(ResultOut):
    student_name: str
    student_email: str
    exam_title: str

    model_config = ConfigDict(from_attributes=True)
