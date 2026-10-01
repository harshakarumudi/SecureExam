from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_client_ip, get_current_user, get_db, require_role
from backend.app.models.user import User, UserRole
from backend.app.schemas.attempt import (
    AnswerAutoSaveRequest,
    AnswerAutoSaveResponse,
    AttemptOut,
    AttemptStartResponse,
    AttemptStatusResponse,
    AttemptSubmitRequest,
    ExamViolationOut,
    ExamViolationRequest,
    ExamViolationResponse,
)
from backend.app.schemas.result import ResultOut
from backend.app.services.attempt_service import AttemptService
from backend.app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/attempts", tags=["Exam Attempts"])


@router.get("/active/{exam_id}", response_model=AttemptStartResponse | None)
async def get_active_exam_attempt(
    exam_id: int,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db)
):
    return await AttemptService.get_active_attempt(db, exam_id=exam_id, student=current_user)


@router.post("/start/{exam_id}", response_model=AttemptStartResponse, status_code=status.HTTP_201_CREATED)
async def start_exam_attempt(
    exam_id: int,
    request: Request,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent")
    return await AttemptService.start_attempt(db, exam_id=exam_id, student=current_user, ip_address=ip, user_agent=ua)


@router.post("/{attempt_id}/save-answer", response_model=AnswerAutoSaveResponse)
async def save_exam_answer(
    attempt_id: int,
    save_req: AnswerAutoSaveRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await AttemptService.save_answer(
        db=db,
        attempt_id=attempt_id,
        student=current_user,
        req=save_req,
        ip_address=ip
    )


@router.post("/{attempt_id}/violation", response_model=ExamViolationResponse)
async def report_exam_violation(
    attempt_id: int,
    violation_req: ExamViolationRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent")
    return await AttemptService.record_violation(
        db=db,
        attempt_id=attempt_id,
        student=current_user,
        req=violation_req,
        ip_address=ip,
        user_agent=ua
    )


@router.get("/{attempt_id}/status", response_model=AttemptStatusResponse)
async def get_attempt_status(
    attempt_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await AttemptService.get_attempt_status(
        db=db,
        attempt_id=attempt_id,
        current_user=current_user,
        ip_address=ip
    )


@router.get("/{attempt_id}/violations", response_model=list[ExamViolationOut])
async def get_attempt_violations(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await AttemptService.get_attempt_violations(
        db=db,
        attempt_id=attempt_id,
        current_user=current_user
    )


@router.post("/{attempt_id}/submit", response_model=ResultOut)
async def submit_exam_attempt(
    attempt_id: int,
    submission: AttemptSubmitRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
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
