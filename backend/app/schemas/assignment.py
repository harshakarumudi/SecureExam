from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExamAssignRequest(BaseModel):
    student_ids: list[int]


class ExamAssignmentOut(BaseModel):
    id: int
    exam_id: int
    student_id: int
    student_name: str
    student_email: str
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)
