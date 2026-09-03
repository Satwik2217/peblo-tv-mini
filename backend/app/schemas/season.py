from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SeasonCreate(BaseModel):
    show_id: int
    season_number: int
    title: Optional[str] = None


class SeasonUpdate(BaseModel):
    season_number: Optional[int] = None
    title: Optional[str] = None


class SeasonResponse(BaseModel):
    id: int
    show_id: int
    season_number: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    episodes_count: int = 0

    class Config:
        from_attributes = True


class SeasonListResponse(BaseModel):
    items: List[SeasonResponse]
    total: int
