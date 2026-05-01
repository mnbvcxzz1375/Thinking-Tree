"""Suggestion schemas for tree analysis and recommendations."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SuggestionType(str, Enum):
    """Types of suggestions the system can generate."""
    MERGE = "merge"              # Merge similar ideas
    SPLIT = "split"              # Split complex ideas
    NEW_DIRECTION = "new_direction"  # Add missing directions
    REBALANCE = "rebalance"      # Rebalance tree structure
    CONNECT = "connect"          # Connect related ideas


class SuggestionPriority(str, Enum):
    """Priority levels for suggestions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SuggestionStatus(str, Enum):
    """Status of a suggestion."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISMISSED = "dismissed"


class TreeNodeBrief(BaseModel):
    """Brief tree node info for suggestion context."""
    id: int
    content: str
    node_type: str
    parent_id: Optional[int] = None


class SuggestionBase(BaseModel):
    """Base suggestion schema."""
    suggestion_type: SuggestionType
    priority: SuggestionPriority = SuggestionPriority.MEDIUM
    title: str = Field(..., min_length=1, max_length=200, description="Suggestion title")
    description: str = Field(..., min_length=1, max_length=2000, description="Detailed description")
    reasoning: str = Field(..., min_length=1, max_length=1000, description="Why this suggestion")


class SuggestionCreate(SuggestionBase):
    """Schema for creating a suggestion."""
    activity_id: int = Field(..., description="Activity ID")
    related_node_ids: List[int] = Field(default_factory=list, description="Related node IDs")
    suggested_content: Optional[str] = Field(None, max_length=5000, description="Suggested new content")
    suggested_parent_id: Optional[int] = Field(None, description="Suggested parent node ID")


class SuggestionResponse(SuggestionBase):
    """Suggestion response schema."""
    id: int
    activity_id: int
    status: SuggestionStatus
    related_node_ids: List[int]
    suggested_content: Optional[str] = None
    suggested_parent_id: Optional[int] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class SuggestionAction(BaseModel):
    """Schema for accepting/rejecting a suggestion."""
    action: str = Field(..., description="Action: accept, reject, dismiss")
    feedback: Optional[str] = Field(None, max_length=1000, description="Teacher feedback")


class SuggestionListResponse(BaseModel):
    """Response for listing suggestions."""
    suggestions: List[SuggestionResponse]
    total: int
    pending_count: int


class TreeAnalysisResult(BaseModel):
    """Result of tree analysis."""
    total_nodes: int
    max_depth: int
    balance_score: float = Field(..., ge=0.0, le=1.0, description="Balance score 0-1")
    node_type_distribution: dict[str, int]
    orphan_count: int
    deep_branch_count: int
    suggestions: List[SuggestionResponse]
