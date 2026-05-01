"""SpeechRecord model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class SpeechRecord(Base):
    """SpeechRecord model for storing speech interactions."""

    __tablename__ = "speech_records"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False, index=True)
    tree_node_id = Column(Integer, ForeignKey("tree_nodes.id"), nullable=True, index=True)
    user_input = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)
    audio_url = Column(String(500), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    activity = relationship("Activity", back_populates="speech_records")
    tree_node = relationship("TreeNode", back_populates="speech_records")

    # Indexes
    __table_args__ = (
        Index("idx_speech_record_activity_id", "activity_id"),
        Index("idx_speech_record_tree_node_id", "tree_node_id"),
        Index("idx_speech_record_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<SpeechRecord(id={self.id}, activity_id={self.activity_id})>"
