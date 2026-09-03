import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class PublishStatus(str, enum.Enum):
    success = "success"
    failed = "failed"


class PublishRun(Base):
    __tablename__ = "publish_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(Enum(PublishStatus), nullable=False, default=PublishStatus.failed)
    shows_count = Column(Integer, default=0)
    episodes_count = Column(Integer, default=0)
    catalogue_version = Column(String(255), nullable=True)
    errors = Column(Text, nullable=True)

    initiator = relationship("User", back_populates="publish_runs")
