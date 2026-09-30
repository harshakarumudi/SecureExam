from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db, get_current_user, get_client_ip
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, TokenResponse
from backend.app.schemas.user import UserCreate, UserOut
from backend.app.services.auth_service import AuthService
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    user = await AuthService.register(db, user_in, ip_address=ip)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_in: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await AuthService.authenticate(db, login_in, ip_address=ip)


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    await AuditService.log_event(
        db=db,
        action="LOGOUT",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        ip_address=ip,
        status="SUCCESS",
        details="User logged out"
    )
    return {"message": "Logged out successfully"}
