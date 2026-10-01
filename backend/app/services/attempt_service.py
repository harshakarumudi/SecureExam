from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.attempt import AttemptStatus, ExamAttempt, ExamViolation, StudentAnswer
from backend.app.models.exam import Exam, ExamAssignment, ExamStatus
from backend.app.models.question import Question
from backend.app.models.user import User, UserRole
from backend.app.schemas.attempt import (
    AnswerAutoSaveRequest,
    AnswerAutoSaveResponse,
    AttemptStartResponse,
    AttemptStatusResponse,
    ExamAttemptMonitorOut,
    ExamViolationOut,
    ExamViolationRequest,
    ExamViolationResponse,
    SavedAnswerItem,
)
from backend.app.schemas.question import OptionCandidateOut, QuestionCandidateOut
from backend.app.services.audit_service import AuditService
from backend.app.services.evaluation_service import EvaluationService


class AttemptService:
    @staticmethod
    async def start_attempt(
        db: AsyncSession,
        exam_id: int,
        student: User,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> AttemptStartResponse:
        # 1. Fetch exam with questions and options
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

        # 2. Check student assignment eligibility (if specific assignments configured)
        assign_count_res = await db.execute(
            select(func.count(ExamAssignment.id)).where(ExamAssignment.exam_id == exam_id)
        )
        total_assignments = assign_count_res.scalar() or 0
        if total_assignments > 0:
            is_assigned_res = await db.execute(
                select(ExamAssignment).where(
                    ExamAssignment.exam_id == exam_id,
                    ExamAssignment.student_id == student.id
                )
            )
            if not is_assigned_res.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to take this examination."
                )

        # 3. Check for existing attempts (Strict One-Attempt Enforcement)
        existing_res = await db.execute(
            select(ExamAttempt)
            .options(selectinload(ExamAttempt.answers))
            .where(
                ExamAttempt.exam_id == exam_id,
                ExamAttempt.student_id == student.id
            )
        )
        existing_attempt = existing_res.scalars().first()
        if existing_attempt:
            # Check terminal states: no retakes permitted
            if existing_attempt.status in [AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already completed and submitted this examination. Retakes are prohibited."
                )
            if existing_attempt.status == AttemptStatus.TERMINATED_FOR_VIOLATION:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Exam terminated due to exceeding the maximum number of allowed violations. Retakes are prohibited."
                )
            if existing_attempt.status == AttemptStatus.EXPIRED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Examination attempt has expired. Retakes are prohibited."
                )

            # In-progress attempt: check authoritative expiration
            if existing_attempt.status == AttemptStatus.IN_PROGRESS:
                now = datetime.now(UTC)
                exp_at = existing_attempt.expires_at.replace(tzinfo=UTC) if existing_attempt.expires_at.tzinfo is None else existing_attempt.expires_at
                grace_period = timedelta(seconds=15)
                if now > exp_at + grace_period:
                    # Auto-submit and seal result
                    existing_attempt.status = AttemptStatus.AUTO_SUBMITTED
                    existing_attempt.termination_reason = "Auto-submitted upon timer expiration."
                    existing_attempt.submitted_at = exp_at
                    await db.commit()
                    await EvaluationService.evaluate_and_seal_existing_answers(
                        db=db,
                        attempt_id=existing_attempt.id,
                        student=student,
                        ip_address=ip_address,
                        is_auto_submit=True
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Examination time has expired. Your attempt has been automatically submitted."
                    )

                # Active attempt resumption: calculate remaining seconds and load saved answers
                rem_secs = max(0, int((exp_at - now).total_seconds()))
                candidate_qs = AttemptService._build_candidate_questions(exam.questions)
                saved_answers = [
                    SavedAnswerItem(
                        question_id=ans.question_id,
                        selected_option_id=ans.selected_option_id,
                        is_marked_for_review=ans.is_marked_for_review
                    )
                    for ans in existing_attempt.answers
                ]
                return AttemptStartResponse(
                    attempt_id=existing_attempt.id,
                    exam_id=exam.id,
                    exam_title=exam.title,
                    duration_minutes=exam.duration_minutes,
                    total_marks=exam.total_marks,
                    enable_negative_marking=exam.enable_negative_marking,
                    started_at=existing_attempt.started_at,
                    expires_at=existing_attempt.expires_at,
                    remaining_seconds=rem_secs,
                    violation_count=existing_attempt.violation_count,
                    status=existing_attempt.status,
                    questions=candidate_qs,
                    saved_answers=saved_answers
                )

        # 4. Initialize new authoritative server-side attempt
        started_at = datetime.now(UTC)
        expires_at = started_at + timedelta(minutes=exam.duration_minutes)

        attempt = ExamAttempt(
            student_id=student.id,
            exam_id=exam.id,
            started_at=started_at,
            expires_at=expires_at,
            status=AttemptStatus.IN_PROGRESS,
            violation_count=0,
            accepted_rules=True
        )
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)

        # Log security audit and start event
        await AuditService.log_event(
            db=db,
            action="EXAM_STARTED",
            actor_id=student.id,
            actor_role=student.role.value,
            resource_id=str(attempt.id),
            ip_address=ip_address,
            status="SUCCESS",
            details=f"Candidate accepted rules and started attempt #{attempt.id} for exam '{exam.title}'"
        )

        violation_log = ExamViolation(
            attempt_id=attempt.id,
            student_id=student.id,
            exam_id=exam.id,
            event_type="EXAM_STARTED",
            warning_number=0,
            details="Exam session initiated under secure full-screen mode.",
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=started_at
        )
        db.add(violation_log)
        await db.commit()

        remaining_seconds = int((expires_at - started_at).total_seconds())
        candidate_questions = AttemptService._build_candidate_questions(exam.questions)

        return AttemptStartResponse(
            attempt_id=attempt.id,
            exam_id=exam.id,
            exam_title=exam.title,
            duration_minutes=exam.duration_minutes,
            total_marks=exam.total_marks,
            enable_negative_marking=exam.enable_negative_marking,
            started_at=started_at,
            expires_at=expires_at,
            remaining_seconds=remaining_seconds,
            violation_count=0,
            status=AttemptStatus.IN_PROGRESS,
            questions=candidate_questions,
            saved_answers=[]
        )

    @staticmethod
    async def save_answer(
        db: AsyncSession,
        attempt_id: int,
        student: User,
        req: AnswerAutoSaveRequest,
        ip_address: str | None = None
    ) -> AnswerAutoSaveResponse:
        # 1. Fetch attempt and verify ownership (IDOR/BOLA Prevention)
        result = await db.execute(select(ExamAttempt).where(ExamAttempt.id == attempt_id))
        attempt = result.scalars().first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")
        if attempt.student_id != student.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot save answer. Attempt status is {attempt.status.value}."
            )

        # 2. Check authoritative timer expiration
        now = datetime.now(UTC)
        exp_at = attempt.expires_at.replace(tzinfo=UTC) if attempt.expires_at.tzinfo is None else attempt.expires_at
        grace_period = timedelta(seconds=15)
        if now > exp_at + grace_period:
            attempt.status = AttemptStatus.AUTO_SUBMITTED
            attempt.termination_reason = "Auto-submitted upon timer expiration."
            attempt.submitted_at = exp_at
            await db.commit()
            await EvaluationService.evaluate_and_seal_existing_answers(
                db=db,
                attempt_id=attempt.id,
                student=student,
                ip_address=ip_address,
                is_auto_submit=True
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Examination time has expired. Attempt was automatically submitted."
            )

        # 3. Upsert StudentAnswer record
        ans_res = await db.execute(
            select(StudentAnswer).where(
                StudentAnswer.attempt_id == attempt.id,
                StudentAnswer.question_id == req.question_id
            )
        )
        db_ans = ans_res.scalars().first()
        if db_ans:
            db_ans.selected_option_id = req.selected_option_id
            db_ans.is_marked_for_review = req.is_marked_for_review
            db_ans.recorded_at = now
        else:
            db_ans = StudentAnswer(
                attempt_id=attempt.id,
                question_id=req.question_id,
                selected_option_id=req.selected_option_id,
                is_marked_for_review=req.is_marked_for_review,
                recorded_at=now
            )
            db.add(db_ans)

        await db.commit()
        await db.refresh(db_ans)

        return AnswerAutoSaveResponse(
            status="saved",
            question_id=db_ans.question_id,
            selected_option_id=db_ans.selected_option_id,
            is_marked_for_review=db_ans.is_marked_for_review,
            recorded_at=db_ans.recorded_at
        )

    @staticmethod
    async def record_violation(
        db: AsyncSession,
        attempt_id: int,
        student: User,
        req: ExamViolationRequest,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> ExamViolationResponse:
        # 1. Fetch attempt and verify ownership
        result = await db.execute(select(ExamAttempt).where(ExamAttempt.id == attempt_id))
        attempt = result.scalars().first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")
        if attempt.student_id != student.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        if attempt.status != AttemptStatus.IN_PROGRESS:
            return ExamViolationResponse(
                violation_count=attempt.violation_count,
                warning_level=min(attempt.violation_count, 4),
                message="Exam terminated due to exceeding the maximum number of allowed violations." if attempt.status == AttemptStatus.TERMINATED_FOR_VIOLATION else f"Attempt is already {attempt.status.value}.",
                is_terminated=(attempt.status == AttemptStatus.TERMINATED_FOR_VIOLATION),
                termination_reason=attempt.termination_reason or "Maximum exam violations exceeded",
                timestamp=datetime.now(UTC)
            )

        now = datetime.now(UTC)
        attempt.violation_count += 1
        count = attempt.violation_count

        is_terminated = False
        term_reason = None

        if count == 1:
            msg = "Warning 1 of 3: You left the examination window or exited full-screen. Further violations may terminate your exam."
            warn_num = 1
        elif count == 2:
            msg = "Warning 2 of 3: Leaving the examination window again may result in exam termination."
            warn_num = 2
        elif count == 3:
            msg = "Final Warning: One more violation will permanently terminate this examination."
            warn_num = 3
        else:
            is_terminated = True
            warn_num = 4
            term_reason = "Maximum exam violations exceeded"
            attempt.status = AttemptStatus.TERMINATED_FOR_VIOLATION
            attempt.termination_reason = term_reason
            attempt.terminated_at = now
            attempt.submitted_at = now
            msg = "Exam Terminated: Exam terminated due to exceeding the maximum number of allowed violations."

        # Record violation in audit log
        violation_log = ExamViolation(
            attempt_id=attempt.id,
            student_id=student.id,
            exam_id=attempt.exam_id,
            event_type=req.event_type,
            warning_number=warn_num,
            details=req.details or f"Violation #{count}: {req.event_type}",
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=now
        )
        db.add(violation_log)
        await db.commit()

        if is_terminated:
            # Automatically evaluate and seal result
            await EvaluationService.evaluate_and_seal_existing_answers(
                db=db,
                attempt_id=attempt.id,
                student=student,
                ip_address=ip_address,
                is_terminated=True
            )
            await AuditService.log_event(
                db=db,
                action="EXAM_TERMINATED",
                actor_id=student.id,
                actor_role=student.role.value,
                resource_id=str(attempt.id),
                ip_address=ip_address,
                status="TERMINATED",
                details=f"Exam terminated on 4th violation: {req.event_type}"
            )
        else:
            await AuditService.log_event(
                db=db,
                action="WARNING_ISSUED",
                actor_id=student.id,
                actor_role=student.role.value,
                resource_id=str(attempt.id),
                ip_address=ip_address,
                status="WARNING",
                details=f"Warning {count}/3 issued for {req.event_type}"
            )

        return ExamViolationResponse(
            violation_count=count,
            warning_level=warn_num,
            message=msg,
            is_terminated=is_terminated,
            termination_reason=term_reason,
            timestamp=now
        )

    @staticmethod
    async def get_attempt_status(
        db: AsyncSession,
        attempt_id: int,
        current_user: User,
        ip_address: str | None = None
    ) -> AttemptStatusResponse:
        result = await db.execute(select(ExamAttempt).where(ExamAttempt.id == attempt_id))
        attempt = result.scalars().first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")

        # IDOR/BOLA Check
        if attempt.student_id != current_user.id and current_user.role not in [UserRole.FACULTY, UserRole.ADMIN]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        now = datetime.now(UTC)
        exp_at = attempt.expires_at.replace(tzinfo=UTC) if attempt.expires_at.tzinfo is None else attempt.expires_at

        # Check if in-progress attempt has expired
        if attempt.status == AttemptStatus.IN_PROGRESS:
            grace_period = timedelta(seconds=15)
            if now > exp_at + grace_period:
                attempt.status = AttemptStatus.AUTO_SUBMITTED
                attempt.termination_reason = "Auto-submitted upon timer expiration."
                attempt.submitted_at = exp_at
                await db.commit()
                await EvaluationService.evaluate_and_seal_existing_answers(
                    db=db,
                    attempt_id=attempt.id,
                    student=current_user,
                    ip_address=ip_address,
                    is_auto_submit=True
                )
                return AttemptStatusResponse(
                    attempt_id=attempt.id,
                    status=AttemptStatus.AUTO_SUBMITTED,
                    remaining_seconds=0,
                    violation_count=attempt.violation_count,
                    is_terminated=False,
                    termination_reason="Time expired; automatically submitted.",
                    expires_at=attempt.expires_at
                )

            rem_secs = max(0, int((exp_at - now).total_seconds()))
            return AttemptStatusResponse(
                attempt_id=attempt.id,
                status=attempt.status,
                remaining_seconds=rem_secs,
                violation_count=attempt.violation_count,
                is_terminated=False,
                termination_reason=None,
                expires_at=attempt.expires_at
            )

        if attempt.status == AttemptStatus.TERMINATED_FOR_VIOLATION:
            return AttemptStatusResponse(
                attempt_id=attempt.id,
                status=attempt.status,
                remaining_seconds=0,
                violation_count=attempt.violation_count,
                is_terminated=True,
                termination_reason=attempt.termination_reason,
                expires_at=attempt.expires_at
            )

        return AttemptStatusResponse(
            attempt_id=attempt.id,
            status=attempt.status,
            remaining_seconds=0,
            violation_count=attempt.violation_count,
            is_terminated=False,
            termination_reason=attempt.termination_reason,
            expires_at=attempt.expires_at
        )

    @staticmethod
    async def get_exam_attempts(db: AsyncSession, exam_id: int, current_user: User) -> list[ExamAttemptMonitorOut]:
        # Verify exam ownership or admin
        exam_res = await db.execute(select(Exam).where(Exam.id == exam_id))
        exam = exam_res.scalars().first()
        if not exam:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found.")
        if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this exam.")

        # Query attempts with user and result
        res = await db.execute(
            select(ExamAttempt)
            .options(selectinload(ExamAttempt.student), selectinload(ExamAttempt.result))
            .where(ExamAttempt.exam_id == exam_id)
            .order_by(ExamAttempt.started_at.desc())
        )
        attempts = res.scalars().all()

        output: list[ExamAttemptMonitorOut] = []
        for att in attempts:
            sc = att.result.total_score if att.result else None
            msc = att.result.max_score if att.result else None
            pct = att.result.percentage if att.result else None
            pas = att.result.passed if att.result else None

            output.append(
                ExamAttemptMonitorOut(
                    id=att.id,
                    student_id=att.student_id,
                    student_name=att.student.full_name if att.student else "Unknown",
                    student_email=att.student.email if att.student else "Unknown",
                    status=att.status,
                    started_at=att.started_at,
                    submitted_at=att.submitted_at,
                    terminated_at=att.terminated_at,
                    termination_reason=att.termination_reason,
                    violation_count=att.violation_count,
                    score=sc,
                    max_score=msc,
                    percentage=pct,
                    passed=pas
                )
            )
        return output

    @staticmethod
    async def get_attempt_violations(db: AsyncSession, attempt_id: int, current_user: User) -> list[ExamViolationOut]:
        res = await db.execute(
            select(ExamAttempt)
            .options(selectinload(ExamAttempt.exam))
            .where(ExamAttempt.id == attempt_id)
        )
        attempt = res.scalars().first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")

        # Authorization: Student owner, Exam faculty creator, or Admin
        if (
            attempt.student_id != current_user.id
            and attempt.exam.created_by != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        viol_res = await db.execute(
            select(ExamViolation)
            .options(selectinload(ExamViolation.student))
            .where(ExamViolation.attempt_id == attempt_id)
            .order_by(ExamViolation.timestamp.asc())
        )
        violations = viol_res.scalars().all()

        return [
            ExamViolationOut(
                id=v.id,
                attempt_id=v.attempt_id,
                student_id=v.student_id,
                student_name=v.student.full_name if v.student else None,
                event_type=v.event_type,
                warning_number=v.warning_number,
                details=v.details,
                ip_address=v.ip_address,
                timestamp=v.timestamp
            )
            for v in violations
        ]

    @staticmethod
    def _build_candidate_questions(questions: list[Question]) -> list[QuestionCandidateOut]:
        candidate_questions: list[QuestionCandidateOut] = []
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
        if attempt.student_id != student.id and student.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        return attempt
