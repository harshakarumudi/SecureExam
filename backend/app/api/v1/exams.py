
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import (
    get_client_ip,
    get_current_user,
    get_db,
    require_roles,
)
from backend.app.models.exam import ExamStatus
from backend.app.models.user import User, UserRole
from backend.app.schemas.assignment import ExamAssignmentOut, ExamAssignRequest
from backend.app.schemas.exam import (
    ExamCandidateOut,
    ExamCreate,
    ExamDetailOut,
    ExamOut,
    ExamUpdate,
)
from backend.app.schemas.question import QuestionCreate, QuestionOut
from backend.app.services.exam_service import ExamService

router = APIRouter(prefix="/exams", tags=["Examinations"])


@router.post("/", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
async def create_exam(
    request: Request,
    exam_in: ExamCreate,
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await ExamService.create_exam(db, exam_in, creator=current_user, ip_address=ip)


@router.get("/", response_model=list[ExamOut])
async def list_exams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role in [UserRole.FACULTY, UserRole.ADMIN]:
        return await ExamService.list_exams_for_faculty(
            db,
            faculty_id=current_user.id,
            is_admin=(current_user.role == UserRole.ADMIN)
        )
    return await ExamService.list_published_exams_for_students(db, student_id=current_user.id)


@router.get("/available", response_model=list[ExamCandidateOut])
async def list_available_exams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    student_id = current_user.id if current_user.role == UserRole.STUDENT else None
    return await ExamService.list_published_exams_for_students(db, student_id=student_id)


@router.get("/{id}", response_model=ExamDetailOut)
async def get_exam(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    exam = await ExamService.get_exam_by_id(db, id)
    # If student, ensure exam is published
    if current_user.role == UserRole.STUDENT and exam.status != ExamStatus.PUBLISHED:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not available.")
    return exam


@router.put("/{id}", response_model=ExamOut)
async def update_exam(
    id: int,
    exam_in: ExamUpdate,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await ExamService.update_exam(db, id, exam_in, current_user=current_user, ip_address=ip)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    id: int,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    await ExamService.delete_exam(db, id, current_user=current_user, ip_address=ip)


@router.post("/{id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def add_question_to_exam(
    id: int,
    question_in: QuestionCreate,
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    return await ExamService.add_question(db, exam_id=id, q_in=question_in, current_user=current_user)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    await ExamService.delete_question(db, question_id, current_user=current_user)


@router.post("/{id}/assignments", response_model=list[ExamAssignmentOut])
async def assign_students(
    id: int,
    assignment_in: ExamAssignRequest,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await ExamService.assign_students_to_exam(
        db,
        exam_id=id,
        student_ids=assignment_in.student_ids,
        current_user=current_user,
        ip_address=ip
    )


@router.get("/{id}/assignments", response_model=list[ExamAssignmentOut])
async def get_assignments(
    id: int,
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    return await ExamService.get_exam_assignments(db, exam_id=id, current_user=current_user)

