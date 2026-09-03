from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ShowCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    synopsis: Optional[str] = None
    section: Optional[str] = None
    categories: Optional[List[str]] = None
    status: str = "draft"


class ShowUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    synopsis: Optional[str] = None
    section: Optional[str] = None
    categories: Optional[List[str]] = None
    status: Optional[str] = None


class ShowResponse(BaseModel):
    id: int
    title: str
    slug: str
    synopsis: Optional[str]
    section: Optional[str]
    categories: Optional[List[str]]
    status: str
    created_at: datetime
    updated_at: datetime
    seasons_count: int = 0
    episodes_count: int = 0

    class Config:
        from_attributes = True


class ShowListResponse(BaseModel):
    items: List[ShowResponse]
    total: int
    page: int
    page_size: int
    pages: int
