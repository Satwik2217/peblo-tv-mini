from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class PublishRunResponse(BaseModel):
    id: int
    initiated_by: int
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    shows_count: int
    episodes_count: int
    catalogue_version: Optional[str]
    errors: Optional[str]
    initiator_email: Optional[str] = None

    class Config:
        from_attributes = True


class PublishRunListResponse(BaseModel):
    items: List[PublishRunResponse]
    total: int
