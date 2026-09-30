from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User
from backend.app.models.exam import Exam
from backend.app.models.question import Question, QuestionOption
from backend.app.models.attempt import ExamAttempt, AttemptStatus, StudentAnswer
from backend.app.models.result import Result
from backend.app.schemas.attempt import AttemptSubmitRequest
from backend.app.schemas.result import ResultOut
from backend.app.services.audit_service import AuditService


class EvaluationService:
    @staticmethod
    async def evaluate_and_seal(
        db: AsyncSession,
        attempt_id: int,
        submission: AttemptSubmitRequest,
        student: User,
        ip_address: Optional[str] = None,
        apply_negative_marking: bool = False
    ) -> ResultOut:
        # 1. Fetch attempt and exam
        result = await db.execute(
            select(ExamAttempt)
            .options(selectinload(ExamAttempt.exam).selectinload(Exam.questions).selectinload(Question.options))
            .where(ExamAttempt.id == attempt_id)
        )
        attempt = result.scalars().first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam attempt not found.")

        # 2. Strict Object-Level Authorization (BOLA/IDOR prevention)
        if attempt.student_id != student.id:
            await AuditService.log_event(
                db=db,
                action="UNAUTHORIZED_SUBMISSION_ATTEMPT",
                actor_id=student.id,
                actor_role=student.role.value,
                resource_id=str(attempt_id),
                ip_address=ip_address,
                status="BLOCKED",
                details=f"Student {student.id} tried to submit attempt owned by {attempt.student_id}"
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this attempt.")

        # 3. Check if already submitted
        if attempt.status == AttemptStatus.SUBMITTED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt has already been submitted.")

        # 4. Authoritative Server Timer Expiration Check
        now = datetime.now(timezone.utc)
        expires_at = attempt.expires_at.replace(tzinfo=timezone.utc) if attempt.expires_at.tzinfo is None else attempt.expires_at
        grace_period = timedelta(seconds=15)
        if now > expires_at + grace_period:
            attempt.status = AttemptStatus.EXPIRED
            await db.commit()

            await AuditService.log_event(
                db=db,
                action="ATTEMPT_EXPIRED_REJECTED",
                actor_id=student.id,
                actor_role=student.role.value,
                resource_id=str(attempt_id),
                ip_address=ip_address,
                status="REJECTED",
                details="Attempt submitted after authoritative expiration deadline"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exam attempt has expired. Submission rejected."
            )

        exam = attempt.exam
        questions = exam.questions

        # Map candidate selections by question_id
        selected_options_map = {ans.question_id: ans.selected_option_id for ans in submission.answers}

        total_score = 0.0
        max_score = 0.0

        # Persist student answers and evaluate
        for q in questions:
            max_score += q.marks
            chosen_opt_id = selected_options_map.get(q.id)

            # Record answer in database
            db_answer = StudentAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_option_id=chosen_opt_id,
                recorded_at=now
            )
            db.add(db_answer)

            # Find correct option directly from database records
            correct_opt = next((opt for opt in q.options if opt.is_correct), None)
            
            if chosen_opt_id is not None:
                if correct_opt and chosen_opt_id == correct_opt.id:
                    total_score += q.marks
                else:
                    if apply_negative_marking:
                        total_score -= q.negative_marks
                    # In V1.0, wrong answers yield 0 penalty

        total_score = max(0.0, total_score)  # score cannot be negative
        percentage = (total_score / max_score * 100.0) if max_score > 0 else 0.0
        passed = total_score >= exam.passing_marks

        # Mark attempt submitted
        attempt.status = AttemptStatus.SUBMITTED
        attempt.submitted_at = now

        # Create sealed Result record
        db_result = Result(
            attempt_id=attempt.id,
            student_id=student.id,
            exam_id=exam.id,
            total_score=round(total_score, 2),
            max_score=round(max_score, 2),
            percentage=round(percentage, 2),
            passed=passed,
            evaluated_at=now
        )
        db.add(db_result)
        await db.commit()
        await db.refresh(db_result)

        await AuditService.log_event(
            db=db,
            action="ATTEMPT_SUBMITTED",
            actor_id=student.id,
            actor_role=student.role.value,
            resource_id=str(attempt.id),
            ip_address=ip_address,
            status="SUCCESS",
            details=f"Exam '{exam.title}' submitted. Score: {total_score}/{max_score} ({percentage:.1f}%)"
        )

        return ResultOut.model_validate(db_result)

    @staticmethod
    async def get_result_for_attempt(db: AsyncSession, attempt_id: int, current_user: User) -> ResultOut:
        result = await db.execute(
            select(Result)
            .where(Result.attempt_id == attempt_id)
        )
        db_res = result.scalars().first()
        if not db_res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found.")

        # Object-level authorization (IDOR/BOLA prevention)
        if db_res.student_id != current_user.id and current_user.role not in ["FACULTY", "ADMIN"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this result.")

        return ResultOut.model_validate(db_res)

