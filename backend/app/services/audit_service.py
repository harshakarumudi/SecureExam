from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.audit import AuditLog


class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        action: str,
        actor_id: Optional[int] = None,
        actor_role: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[str] = None
    ) -> AuditLog:
        """Appends an immutable security audit record to the audit_logs table."""
        audit_entry = AuditLog(
            action=action,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_id=resource_id,
            ip_address=ip_address,
            status=status,
            details=details
        )
        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)
        return audit_entry
