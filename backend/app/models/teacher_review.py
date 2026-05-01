"""TeacherReview model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class TeacherReview(Base):
    """TeacherReview model for teacher feedback on tree nodes."""

    __tablename__ = "teacher_reviews"

    id = Column(Integer, primary_key=True, index=True)
    tree_node_id = Column(Integer, ForeignKey("tree_nodes.id"), nullable=False, index=True)
    teacher_name = Column(String(255), nullable=False)
    feedback = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    is_approved = Column(Integer, default=0)  # 0: pending, 1: approved, -1: rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tree_node = relationship("TreeNode", back_populates="teacher_reviews")

    # Indexes
    __table_args__ = (
        Index("idx_teacher_review_tree_node_id", "tree_node_id"),
        Index("idx_teacher_review_is_approved", "is_approved"),
        Index("idx_teacher_review_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TeacherReview(id={self.id}, tree_node_id={self.tree_node_id})>"
