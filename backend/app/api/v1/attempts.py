from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db, get_current_user, require_role, get_client_ip
from backend.app.models.user import User, UserRole
from backend.app.schemas.attempt import AttemptStartResponse, AttemptSubmitRequest, AttemptOut
from backend.app.schemas.result import ResultOut
from backend.app.services.attempt_service import AttemptService
from backend.app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/attempts", tags=["Exam Attempts"])


@router.post("/start/{exam_id}", response_model=AttemptStartResponse, status_code=status.HTTP_201_CREATED)
async def start_exam_attempt(
    exam_id: int,
    request: Request,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await AttemptService.start_attempt(db, exam_id=exam_id, student=current_user, ip_address=ip)


@router.post("/{attempt_id}/submit", response_model=ResultOut)
async def submit_exam_attempt(
    attempt_id: int,
    submission: AttemptSubmitRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    # Server-Authoritative Evaluation (positive marking in V1.0)
    return await EvaluationService.evaluate_and_seal(
        db=db,
        attempt_id=attempt_id,
        submission=submission,
        student=current_user,
        ip_address=ip,
        apply_negative_marking=False
    )


@router.get("/{attempt_id}", response_model=AttemptOut)
async def get_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await AttemptService.get_attempt_for_student(db, attempt_id=attempt_id, student=current_user)
