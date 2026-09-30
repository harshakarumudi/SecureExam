from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    actor_id: Optional[int] = None
    actor_role: Optional[str] = None
    action: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    status: str
    details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
