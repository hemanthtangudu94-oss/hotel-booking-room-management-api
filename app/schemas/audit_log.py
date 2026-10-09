from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity: str
    entity_id: int
    old_value: str | None
    new_value: str | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)