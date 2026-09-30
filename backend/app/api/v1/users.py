
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_client_ip, get_db, require_role
from backend.app.models.user import User, UserRole
from backend.app.schemas.user import UserOut, UserRoleUpdate, UserStatusUpdate
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/users", tags=["User Governance (Admin)"])


@router.get("/", response_model=list[UserOut])
async def list_users(
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).order_by(User.id.asc()))
    return result.scalars().all()


@router.put("/{id}/role", response_model=UserOut)
async def update_user_role(
    id: int,
    role_in: UserRoleUpdate,
    request: Request,
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    old_role = target_user.role
    target_user.role = role_in.role
    await db.commit()
    await db.refresh(target_user)

    ip = get_client_ip(request)
    await AuditService.log_event(
        db=db,
        action="ROLE_CHANGED",
        actor_id=current_admin.id,
        actor_role=current_admin.role.value,
        resource_id=str(target_user.id),
        ip_address=ip,
        status="SUCCESS",
        details=f"User {target_user.email} role changed from {old_role} to {role_in.role}"
    )
    return target_user


@router.put("/{id}/status", response_model=UserOut)
async def toggle_user_status(
    id: int,
    status_in: UserStatusUpdate,
    request: Request,
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target_user.is_active = status_in.is_active
    await db.commit()
    await db.refresh(target_user)

    ip = get_client_ip(request)
    status_str = "ACTIVATED" if status_in.is_active else "DEACTIVATED"
    await AuditService.log_event(
        db=db,
        action=f"USER_{status_str}",
        actor_id=current_admin.id,
        actor_role=current_admin.role.value,
        resource_id=str(target_user.id),
        ip_address=ip,
        status="SUCCESS",
        details=f"User {target_user.email} status set to {status_in.is_active}"
    )
    return target_user
