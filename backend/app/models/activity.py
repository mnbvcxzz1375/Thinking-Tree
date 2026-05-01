"""Activity model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Activity(Base):
    """Activity model for thinking tree activities."""

    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    difficulty_level = Column(String(50), nullable=False, default="medium")
    age_group = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tree_nodes = relationship("TreeNode", back_populates="activity", cascade="all, delete-orphan")
    speech_records = relationship("SpeechRecord", back_populates="activity", cascade="all, delete-orphan")
    suggestions = relationship("Suggestion", back_populates="activity", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_activity_is_active", "is_active"),
        Index("idx_activity_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Activity(id={self.id}, title={self.title})>"
