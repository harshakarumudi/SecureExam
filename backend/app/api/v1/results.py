
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user, get_db, require_roles
from backend.app.models.exam import Exam
from backend.app.models.result import Result
from backend.app.models.user import User, UserRole
from backend.app.schemas.result import ResultDetailOut, ResultOut
from backend.app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/results", tags=["Results & Grades"])


@router.get("/attempt/{attempt_id}", response_model=ResultOut)
async def get_attempt_result(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await EvaluationService.get_result_for_attempt(db, attempt_id=attempt_id, current_user=current_user)


@router.get("/my", response_model=list[ResultOut])
async def get_my_results(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Result)
        .where(Result.student_id == current_user.id)
        .order_by(Result.evaluated_at.desc())
    )
    return result.scalars().all()


@router.get("/exam/{exam_id}", response_model=list[ResultDetailOut])
async def get_exam_results(
    exam_id: int,
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    # Verify faculty owns the exam
    exam_res = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_res.scalars().first()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found.")
    if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    result = await db.execute(
        select(Result)
        .options(selectinload(Result.student), selectinload(Result.exam))
        .where(Result.exam_id == exam_id)
        .order_by(Result.evaluated_at.desc())
    )
    results = result.scalars().all()

    out: list[ResultDetailOut] = []
    for r in results:
        out.append(
            ResultDetailOut(
                id=r.id,
                attempt_id=r.attempt_id,
                student_id=r.student_id,
                exam_id=r.exam_id,
                total_score=r.total_score,
                max_score=r.max_score,
                percentage=r.percentage,
                passed=r.passed,
                evaluated_at=r.evaluated_at,
                student_name=r.student.full_name,
                student_email=r.student.email,
                exam_title=r.exam.title
            )
        )
    return out
