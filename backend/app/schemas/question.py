
from pydantic import BaseModel, ConfigDict, Field


class OptionBase(BaseModel):
    option_text: str = Field(..., min_length=1)
    order_index: int = 0


class OptionCreate(OptionBase):
    is_correct: bool = False


class OptionOut(OptionBase):
    id: int
    question_id: int
    is_correct: bool

    model_config = ConfigDict(from_attributes=True)


class OptionCandidateOut(OptionBase):
    id: int
    question_id: int

    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    question_text: str = Field(..., min_length=3)
    marks: float = Field(default=1.0, ge=0.1)
    negative_marks: float = Field(default=0.0, ge=0.0)
    explanation: str | None = None
    order_index: int = 0


class QuestionCreate(QuestionBase):
    options: list[OptionCreate] = Field(..., min_length=2, max_length=6)


class QuestionUpdate(BaseModel):
    question_text: str | None = Field(None, min_length=3)
    marks: float | None = Field(None, ge=0.1)
    negative_marks: float | None = Field(None, ge=0.0)
    explanation: str | None = None
    order_index: int | None = None
    options: list[OptionCreate] | None = None


class QuestionOut(QuestionBase):
    id: int
    exam_id: int
    options: list[OptionOut]

    model_config = ConfigDict(from_attributes=True)


class QuestionCandidateOut(BaseModel):
    id: int
    exam_id: int
    question_text: str
    marks: float
    order_index: int
    options: list[OptionCandidateOut]

    model_config = ConfigDict(from_attributes=True)
