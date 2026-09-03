import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class EpisodeStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season_id = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    synopsis = Column(Text, nullable=True)
    episode_number = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    language = Column(String(10), nullable=False)
    content_group = Column(String(500), nullable=False, index=True)
    status = Column(Enum(EpisodeStatus), nullable=False, default=EpisodeStatus.draft)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    season = relationship("Season", back_populates="episodes")
    artworks = relationship("Artwork", back_populates="episode", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("content_group", "language", name="uq_content_group_language"),
    )
