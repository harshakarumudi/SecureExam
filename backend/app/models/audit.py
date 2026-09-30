from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS", nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
