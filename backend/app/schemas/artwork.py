from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ArtworkResponse(BaseModel):
    id: int
    show_id: Optional[int]
    episode_id: Optional[int]
    artwork_type: str
    storage_key: str
    original_filename: Optional[str]
    mime_type: Optional[str]
    file_size: Optional[int]
    width: Optional[int]
    height: Optional[int]
    created_at: datetime
    url: Optional[str] = None

    class Config:
        from_attributes = True
