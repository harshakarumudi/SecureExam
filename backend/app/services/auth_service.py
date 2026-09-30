from datetime import timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    create_access_token
)
from backend.app.models.user import User, UserRole
from backend.app.schemas.user import UserCreate
from backend.app.schemas.auth import LoginRequest, TokenResponse
from backend.app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, user_in: UserCreate, ip_address: Optional[str] = None) -> User:
        # 1. Enforce rigorous password complexity
        is_strong, msg = validate_password_strength(user_in.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=msg
            )

        # 2. Check for existing normalized email
        norm_email = user_in.email.strip().lower()
        result = await db.execute(select(User).where(User.email == norm_email))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )

        # 3. Hash password using Argon2id
        hashed_pwd = get_password_hash(user_in.password)

        # 4. Create and persist user entity
        db_user = User(
            email=norm_email,
            full_name=user_in.full_name.strip(),
            hashed_password=hashed_pwd,
            role=user_in.role or UserRole.STUDENT,
            is_active=True
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        # 5. Log audit event
        await AuditService.log_event(
            db=db,
            action="USER_REGISTERED",
            actor_id=db_user.id,
            actor_role=db_user.role.value,
            resource_id=str(db_user.id),
            ip_address=ip_address,
            status="SUCCESS",
            details=f"User {db_user.email} registered with role {db_user.role.value}"
        )
        return db_user

    @staticmethod
    async def authenticate(db: AsyncSession, login_in: LoginRequest, ip_address: Optional[str] = None) -> TokenResponse:
        norm_email = login_in.email.strip().lower()
        result = await db.execute(select(User).where(User.email == norm_email))
        user = result.scalars().first()

        # Constant-time security check against user enumeration
        is_valid_pwd = False
        if user:
            is_valid_pwd = verify_password(login_in.password, user.hashed_password)
        else:
            # Dummy verify to equalize response timing
            _ = verify_password(login_in.password, "$argon2id$v=19$m=19456,t=2,p=1$ZHVtbXlzYWx0ZHVtbXk$dummyhashdummyhashdummyhashdummyhash")

        if not user or not is_valid_pwd:
            await AuditService.log_event(
                db=db,
                action="LOGIN_FAILED",
                actor_id=user.id if user else None,
                ip_address=ip_address,
                status="FAILURE",
                details=f"Failed login attempt for email {norm_email}"
            )
            # Generic message to prevent account enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            await AuditService.log_event(
                db=db,
                action="LOGIN_BLOCKED",
                actor_id=user.id,
                actor_role=user.role.value,
                ip_address=ip_address,
                status="BLOCKED",
                details="Deactivated account attempted login"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact an administrator."
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
            expires_delta=access_token_expires
        )

        await AuditService.log_event(
            db=db,
            action="LOGIN_SUCCESS",
            actor_id=user.id,
            actor_role=user.role.value,
            resource_id=str(user.id),
            ip_address=ip_address,
            status="SUCCESS",
            details="User logged in successfully"
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )
