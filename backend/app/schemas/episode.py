from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class EpisodeCreate(BaseModel):
    season_id: int
    title: str
    synopsis: Optional[str] = None
    episode_number: int
    duration_seconds: Optional[int] = None
    language: str
    content_group: str
    status: str = "draft"


class EpisodeUpdate(BaseModel):
    title: Optional[str] = None
    synopsis: Optional[str] = None
    episode_number: Optional[int] = None
    duration_seconds: Optional[int] = None
    language: Optional[str] = None
    content_group: Optional[str] = None
    status: Optional[str] = None


class EpisodeResponse(BaseModel):
    id: int
    season_id: int
    title: str
    synopsis: Optional[str]
    episode_number: int
    duration_seconds: Optional[int]
    language: str
    content_group: str
    status: str
    created_at: datetime
    updated_at: datetime
    artworks: List[dict] = []

    class Config:
        from_attributes = True


class EpisodeListResponse(BaseModel):
    items: List[EpisodeResponse]
    total: int
    page: int
    page_size: int
    pages: int
