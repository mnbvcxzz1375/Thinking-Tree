"""TreeNode model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import backref, relationship
from datetime import datetime
from app.database import Base


class TreeNode(Base):
    """TreeNode model for thinking tree nodes."""

    __tablename__ = "tree_nodes"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("tree_nodes.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    node_type = Column(String(50), nullable=False, default="question")  # question, answer, insight
    position_x = Column(Integer, nullable=True)
    position_y = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    activity = relationship("Activity", back_populates="tree_nodes")
    children = relationship(
        "TreeNode",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
        single_parent=True,
    )
    speech_records = relationship("SpeechRecord", back_populates="tree_node", cascade="all, delete-orphan")
    teacher_reviews = relationship("TeacherReview", back_populates="tree_node", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_tree_node_activity_id", "activity_id"),
        Index("idx_tree_node_parent_id", "parent_id"),
        Index("idx_tree_node_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TreeNode(id={self.id}, type={self.node_type})>"
