import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

VALID_SECTIONS = ["featured", "series", "minisodes", "songs"]
VALID_CATEGORIES = [
    "adventure", "folk", "friendship", "india", "language",
    "learning", "maths", "music", "nature", "reading",
    "science", "singalong", "stories", "travel", "values"
]


class ShowStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Show(Base):
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False, unique=True, index=True)
    synopsis = Column(Text, nullable=True)
    section = Column(String(50), nullable=True)
    categories = Column(Text, nullable=True)  # JSON array stored as text
    status = Column(Enum(ShowStatus), nullable=False, default=ShowStatus.draft)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan", order_by="Season.season_number")
    artworks = relationship("Artwork", back_populates="show", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("slug", name="uq_show_slug"),
    )
