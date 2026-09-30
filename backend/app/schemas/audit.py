from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    actor_id: int | None = None
    actor_role: str | None = None
    action: str
    resource_id: str | None = None
    ip_address: str | None = None
    status: str
    details: str | None = None

    model_config = ConfigDict(from_attributes=True)
