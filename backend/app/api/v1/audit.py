from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db, require_role
from backend.app.models.user import User, UserRole
from backend.app.models.audit import AuditLog
from backend.app.schemas.audit import AuditLogOut

router = APIRouter(prefix="/audit", tags=["Security Audit Logs (Admin)"])


@router.get("/", response_model=List[AuditLogOut])
async def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    action: Optional[str] = None,
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    if action:
        query = query.where(AuditLog.action == action)
    result = await db.execute(query)
    return result.scalars().all()
