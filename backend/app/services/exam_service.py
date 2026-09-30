from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.sanitizer import sanitize_html
from backend.app.models.user import User, UserRole
from backend.app.models.exam import Exam, ExamStatus
from backend.app.models.question import Question, QuestionOption
from backend.app.schemas.exam import ExamCreate, ExamUpdate
from backend.app.schemas.question import QuestionCreate, QuestionUpdate
from backend.app.services.audit_service import AuditService


class ExamService:
    @staticmethod
    async def create_exam(db: AsyncSession, exam_in: ExamCreate, creator: User, ip_address: Optional[str] = None) -> Exam:
        clean_title = sanitize_html(exam_in.title)
        clean_desc = sanitize_html(exam_in.description) if exam_in.description else None

        exam = Exam(
            title=clean_title,
            description=clean_desc,
            duration_minutes=exam_in.duration_minutes,
            total_marks=exam_in.total_marks,
            passing_marks=exam_in.passing_marks,
            status=ExamStatus.DRAFT,
            created_by=creator.id,
            start_time=exam_in.start_time,
            end_time=exam_in.end_time
        )
        db.add(exam)
        await db.commit()
        await db.refresh(exam)

        await AuditService.log_event(
            db=db,
            action="EXAM_CREATED",
            actor_id=creator.id,
            actor_role=creator.role.value,
            resource_id=str(exam.id),
            ip_address=ip_address,
            status="SUCCESS",
            details=f"Exam '{exam.title}' created in DRAFT state"
        )
        return exam

    @staticmethod
    async def get_exam_by_id(db: AsyncSession, exam_id: int) -> Exam:
        result = await db.execute(
            select(Exam)
            .options(
                selectinload(Exam.questions).selectinload(Question.options),
                selectinload(Exam.creator)
            )
            .where(Exam.id == exam_id)
        )
        exam = result.scalars().first()
        if not exam:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination not found.")
        return exam

    @staticmethod
    async def list_exams_for_faculty(db: AsyncSession, faculty_id: int, is_admin: bool = False) -> List[Exam]:
        query = select(Exam).options(selectinload(Exam.questions))
        if not is_admin:
            query = query.where(Exam.created_by == faculty_id)
        query = query.order_by(Exam.created_at.desc())
        result = await db.execute(query)
        exams = result.scalars().all()
        # populate question count
        for ex in exams:
            ex.question_count = len(ex.questions)
        return exams

    @staticmethod
    async def list_published_exams_for_students(db: AsyncSession) -> List[Exam]:
        result = await db.execute(
            select(Exam)
            .options(selectinload(Exam.questions))
            .where(Exam.status == ExamStatus.PUBLISHED)
            .order_by(Exam.created_at.desc())
        )
        exams = result.scalars().all()
        for ex in exams:
            ex.question_count = len(ex.questions)
        return exams

    @staticmethod
    async def update_exam(db: AsyncSession, exam_id: int, exam_in: ExamUpdate, current_user: User, ip_address: Optional[str] = None) -> Exam:
        exam = await ExamService.get_exam_by_id(db, exam_id)

        # Enforce Object-Level Authorization (BOLA/IDOR prevention)
        if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
            await AuditService.log_event(
                db=db,
                action="UNAUTHORIZED_EXAM_UPDATE_ATTEMPT",
                actor_id=current_user.id,
                actor_role=current_user.role.value,
                resource_id=str(exam_id),
                ip_address=ip_address,
                status="BLOCKED",
                details=f"User {current_user.id} attempted to edit exam owned by {exam.created_by}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to modify this examination."
            )

        if exam_in.title is not None:
            exam.title = sanitize_html(exam_in.title)
        if exam_in.description is not None:
            exam.description = sanitize_html(exam_in.description)
        if exam_in.duration_minutes is not None:
            exam.duration_minutes = exam_in.duration_minutes
        if exam_in.total_marks is not None:
            exam.total_marks = exam_in.total_marks
        if exam_in.passing_marks is not None:
            exam.passing_marks = exam_in.passing_marks
        if exam_in.status is not None:
            exam.status = exam_in.status
        if exam_in.start_time is not None:
            exam.start_time = exam_in.start_time
        if exam_in.end_time is not None:
            exam.end_time = exam_in.end_time

        await db.commit()
        await db.refresh(exam)

        await AuditService.log_event(
            db=db,
            action="EXAM_UPDATED",
            actor_id=current_user.id,
            actor_role=current_user.role.value,
            resource_id=str(exam.id),
            ip_address=ip_address,
            status="SUCCESS",
            details=f"Exam '{exam.title}' updated"
        )
        return exam

    @staticmethod
    async def delete_exam(db: AsyncSession, exam_id: int, current_user: User, ip_address: Optional[str] = None) -> None:
        exam = await ExamService.get_exam_by_id(db, exam_id)

        # Enforce Object-Level Authorization
        if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
            await AuditService.log_event(
                db=db,
                action="UNAUTHORIZED_EXAM_DELETE_ATTEMPT",
                actor_id=current_user.id,
                actor_role=current_user.role.value,
                resource_id=str(exam_id),
                ip_address=ip_address,
                status="BLOCKED"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this examination."
            )

        await db.delete(exam)
        await db.commit()

        await AuditService.log_event(
            db=db,
            action="EXAM_DELETED",
            actor_id=current_user.id,
            actor_role=current_user.role.value,
            resource_id=str(exam_id),
            ip_address=ip_address,
            status="SUCCESS",
            details=f"Exam ID {exam_id} deleted"
        )

    @staticmethod
    async def add_question(db: AsyncSession, exam_id: int, q_in: QuestionCreate, current_user: User) -> Question:
        exam = await ExamService.get_exam_by_id(db, exam_id)
        if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

        clean_text = sanitize_html(q_in.question_text)
        clean_exp = sanitize_html(q_in.explanation) if q_in.explanation else None

        question = Question(
            exam_id=exam.id,
            question_text=clean_text,
            marks=q_in.marks,
            negative_marks=q_in.negative_marks,
            explanation=clean_exp,
            order_index=q_in.order_index
        )
        db.add(question)
        await db.flush()

        # Add choices
        has_correct = False
        for opt in q_in.options:
            if opt.is_correct:
                has_correct = True
            option = QuestionOption(
                question_id=question.id,
                option_text=sanitize_html(opt.option_text),
                is_correct=opt.is_correct,
                order_index=opt.order_index
            )
            db.add(option)

        if not has_correct:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one option must be marked as correct.")

        await db.commit()
        res = await db.execute(
            select(Question).options(selectinload(Question.options)).where(Question.id == question.id)
        )
        return res.scalars().first()

    @staticmethod
    async def delete_question(db: AsyncSession, question_id: int, current_user: User) -> None:
        result = await db.execute(select(Question).options(selectinload(Question.exam)).where(Question.id == question_id))
        q = result.scalars().first()
        if not q:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
        if q.exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

        await db.delete(q)
        await db.commit()

