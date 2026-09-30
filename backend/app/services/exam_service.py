
from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.sanitizer import sanitize_html
from backend.app.models.exam import Exam, ExamAssignment, ExamStatus
from backend.app.models.question import Question, QuestionOption
from backend.app.models.user import User, UserRole
from backend.app.schemas.exam import ExamCreate, ExamUpdate
from backend.app.schemas.question import QuestionCreate
from backend.app.services.audit_service import AuditService


class ExamService:
    @staticmethod
    async def create_exam(db: AsyncSession, exam_in: ExamCreate, creator: User, ip_address: str | None = None) -> Exam:
        clean_title = sanitize_html(exam_in.title)
        clean_desc = sanitize_html(exam_in.description) if exam_in.description else None

        exam = Exam(
            title=clean_title,
            description=clean_desc,
            duration_minutes=exam_in.duration_minutes,
            total_marks=exam_in.total_marks,
            passing_marks=exam_in.passing_marks,
            enable_negative_marking=exam_in.enable_negative_marking,
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
    async def list_exams_for_faculty(db: AsyncSession, faculty_id: int, is_admin: bool = False) -> list[Exam]:
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
    async def list_published_exams_for_students(db: AsyncSession, student_id: int | None = None) -> list[Exam]:
        result = await db.execute(
            select(Exam)
            .options(
                selectinload(Exam.questions),
                selectinload(Exam.assignments)
            )
            .where(Exam.status == ExamStatus.PUBLISHED)
            .order_by(Exam.created_at.desc())
        )
        exams = result.scalars().all()
        filtered = []
        for ex in exams:
            ex.question_count = len(ex.questions)
            if not ex.assignments:
                filtered.append(ex)
            elif student_id is not None and any(a.student_id == student_id for a in ex.assignments):
                filtered.append(ex)
        return filtered

    @staticmethod
    async def update_exam(db: AsyncSession, exam_id: int, exam_in: ExamUpdate, current_user: User, ip_address: str | None = None) -> Exam:
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
        if exam_in.enable_negative_marking is not None:
            exam.enable_negative_marking = exam_in.enable_negative_marking
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
    async def delete_exam(db: AsyncSession, exam_id: int, current_user: User, ip_address: str | None = None) -> None:
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

    @staticmethod
    async def assign_students_to_exam(
        db: AsyncSession,
        exam_id: int,
        student_ids: list[int],
        current_user: User,
        ip_address: str | None = None
    ) -> list[dict]:
        exam = await ExamService.get_exam_by_id(db, exam_id)
        if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to assign students to this exam."
            )

        # Clear existing assignments
        await db.execute(delete(ExamAssignment).where(ExamAssignment.exam_id == exam_id))

        # Insert new assignments
        new_assignments = []
        for sid in student_ids:
            s_res = await db.execute(select(User).where(User.id == sid, User.role == UserRole.STUDENT))
            student = s_res.scalars().first()
            if student:
                assignment = ExamAssignment(exam_id=exam_id, student_id=student.id)
                db.add(assignment)
                new_assignments.append(assignment)

        await db.commit()

        await AuditService.log_event(
            db=db,
            action="EXAM_STUDENTS_ASSIGNED",
            actor_id=current_user.id,
            actor_role=current_user.role.value,
            resource_id=str(exam_id),
            ip_address=ip_address,
            status="SUCCESS",
            details=f"Assigned {len(new_assignments)} students to exam '{exam.title}'"
        )

        return await ExamService.get_exam_assignments(db, exam_id, current_user)

    @staticmethod
    async def get_exam_assignments(db: AsyncSession, exam_id: int, current_user: User) -> list[dict]:
        exam = await ExamService.get_exam_by_id(db, exam_id)
        if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

        res = await db.execute(
            select(ExamAssignment)
            .options(selectinload(ExamAssignment.student))
            .where(ExamAssignment.exam_id == exam_id)
            .order_by(ExamAssignment.assigned_at.asc())
        )
        assignments = res.scalars().all()
        return [
            {
                "id": a.id,
                "exam_id": a.exam_id,
                "student_id": a.student_id,
                "student_name": a.student.full_name if a.student else "Unknown",
                "student_email": a.student.email if a.student else "Unknown",
                "assigned_at": a.assigned_at
            }
            for a in assignments
        ]


