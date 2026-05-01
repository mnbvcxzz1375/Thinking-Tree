"""Suggestion model for storing tree suggestions."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Suggestion(Base):
    """Suggestion model for AI-generated tree recommendations."""

    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False, index=True)
    suggestion_type = Column(String(50), nullable=False)  # merge, split, new_direction, rebalance, connect
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, accepted, rejected, dismissed
    related_node_ids = Column(String(500), nullable=True)  # Comma-separated node IDs
    suggested_content = Column(Text, nullable=True)
    suggested_parent_id = Column(Integer, nullable=True)
    teacher_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    activity = relationship("Activity", back_populates="suggestions")

    # Indexes
    __table_args__ = (
        Index("idx_suggestion_activity_id", "activity_id"),
        Index("idx_suggestion_status", "status"),
        Index("idx_suggestion_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Suggestion(id={self.id}, type={self.suggestion_type}, status={self.status})>"
