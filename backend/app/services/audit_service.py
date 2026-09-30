
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditLog


class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        action: str,
        actor_id: int | None = None,
        actor_role: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        status: str = "SUCCESS",
        details: str | None = None
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
