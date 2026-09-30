from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db, get_current_user, require_role, require_roles, get_client_ip
from backend.app.models.user import User, UserRole
from backend.app.models.exam import ExamStatus
from backend.app.schemas.exam import ExamCreate, ExamUpdate, ExamOut, ExamDetailOut, ExamCandidateOut
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


@router.get("/", response_model=List[ExamOut])
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
    return await ExamService.list_published_exams_for_students(db)


@router.get("/available", response_model=List[ExamCandidateOut])
async def list_available_exams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ExamService.list_published_exams_for_students(db)


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
