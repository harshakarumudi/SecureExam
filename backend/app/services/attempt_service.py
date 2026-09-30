from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User
from backend.app.models.exam import Exam, ExamStatus
from backend.app.models.question import Question, QuestionOption
from backend.app.models.attempt import ExamAttempt, AttemptStatus, StudentAnswer
from backend.app.schemas.attempt import AttemptStartResponse, AttemptSubmitRequest
from backend.app.schemas.question import QuestionCandidateOut, OptionCandidateOut
from backend.app.services.audit_service import AuditService


class AttemptService:
    @staticmethod
    async def start_attempt(db: AsyncSession, exam_id: int, student: User, ip_address: Optional[str] = None) -> AttemptStartResponse:
        # 1. Fetch exam with questions
        result = await db.execute(
            select(Exam)
            .options(selectinload(Exam.questions).selectinload(Question.options))
            .where(Exam.id == exam_id)
        )
        exam = result.scalars().first()
        if not exam or exam.status != ExamStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Examination is not available for attempts."
            )

        # 2. Check for active or already completed attempts
        existing_res = await db.execute(
            select(ExamAttempt).where(
                ExamAttempt.exam_id == exam_id,
                ExamAttempt.student_id == student.id
            )
        )
        existing_attempt = existing_res.scalars().first()
        if existing_attempt:
            if existing_attempt.status == AttemptStatus.SUBMITTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already submitted this examination."
                )
            if existing_attempt.status == AttemptStatus.IN_PROGRESS:
                # If existing attempt has not expired, resume it
                now = datetime.now(timezone.utc)
                if now < existing_attempt.expires_at:
                    rem_secs = max(0, int((existing_attempt.expires_at - now).total_seconds()))
                    candidate_qs = AttemptService._build_candidate_questions(exam.questions)
                    return AttemptStartResponse(
                        attempt_id=existing_attempt.id,
                        exam_id=exam.id,
                        exam_title=exam.title,
                        duration_minutes=exam.duration_minutes,
                        started_at=existing_attempt.started_at,
                        expires_at=existing_attempt.expires_at,
                        remaining_seconds=rem_secs,
                        questions=candidate_qs
                    )

        # 3. Initialize server-authoritative timer
        started_at = datetime.now(timezone.utc)
        expires_at = started_at + timedelta(minutes=exam.duration_minutes)

        attempt = ExamAttempt(
            student_id=student.id,
            exam_id=exam.id,
            started_at=started_at,
            expires_at=expires_at,
            status=AttemptStatus.IN_PROGRESS
        )
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)

        await AuditService.log_event(
            db=db,
            action="ATTEMPT_STARTED",
            actor_id=student.id,
            actor_role=student.role.value,
            resource_id=str(attempt.id),
            ip_address=ip_address,
            status="SUCCESS",
            details=f"Candidate started attempt for exam '{exam.title}'"
        )

        remaining_seconds = int((expires_at - started_at).total_seconds())
        candidate_questions = AttemptService._build_candidate_questions(exam.questions)

        return AttemptStartResponse(
            attempt_id=attempt.id,
            exam_id=exam.id,
            exam_title=exam.title,
            duration_minutes=exam.duration_minutes,
            started_at=started_at,
            expires_at=expires_at,
            remaining_seconds=remaining_seconds,
            questions=candidate_questions
        )

    @staticmethod
    def _build_candidate_questions(questions: List[Question]) -> List[QuestionCandidateOut]:
        candidate_questions: List[QuestionCandidateOut] = []
        for q in sorted(questions, key=lambda x: x.order_index):
            opts = [
                OptionCandidateOut(
                    id=o.id,
                    question_id=o.question_id,
                    option_text=o.option_text,
                    order_index=o.order_index
                )
                for o in sorted(q.options, key=lambda x: x.order_index)
            ]
            candidate_questions.append(
                QuestionCandidateOut(
                    id=q.id,
                    exam_id=q.exam_id,
                    question_text=q.question_text,
                    marks=q.marks,
                    order_index=q.order_index,
                    options=opts
                )
            )
        return candidate_questions

    @staticmethod
    async def get_attempt_for_student(db: AsyncSession, attempt_id: int, student: User) -> ExamAttempt:
        result = await db.execute(
            select(ExamAttempt)
            .options(selectinload(ExamAttempt.answers), selectinload(ExamAttempt.exam))
            .where(ExamAttempt.id == attempt_id)
        )
        attempt = result.scalars().first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")

        # Object-level authorization check (IDOR/BOLA prevention)
        if attempt.student_id != student.id and student.role != "ADMIN":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        return attempt
