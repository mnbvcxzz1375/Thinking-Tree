"""Follow-up question schemas with validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class QuestionCategory(str, Enum):
    """Categories for follow-up questions."""

    EXPLORATION = "exploration"  # Deep exploration of current topic
    CONNECTION = "connection"  # Connecting ideas across branches
    REFLECTION = "reflection"  # Encouraging self-reflection
    CHALLENGE = "challenge"  # Challenging assumptions
    CREATIVE = "creative"  # Creative thinking prompts
    EMPTY_BRANCH = "empty_branch"  # Suggestions for empty branches


class AgeGroup(str, Enum):
    """Age groups for language calibration."""

    YOUNG = "4-6"  # Simple words, concrete examples
    MIDDLE = "7-9"  # Moderate complexity
    OLDER = "10-12"  # Can handle abstract questions


class QuestionRequest(BaseModel):
    """Request schema for generating follow-up questions."""

    node_content: str = Field(
        ..., min_length=1, max_length=5000, description="Content of the node to generate questions for"
    )
    node_type: str = Field(default="answer", description="Type of the node")
    parent_content: Optional[str] = Field(None, description="Content of the parent node for context")
    children_contents: List[str] = Field(default_factory=list, description="Content of child nodes")
    age_group: str = Field(default="7-9", description="Target age group (4-6, 7-9, 10-12)")
    category: Optional[str] = Field(None, description="Preferred question category")
    count: int = Field(default=3, ge=1, le=10, description="Number of questions to generate")

    @field_validator("age_group")
    @classmethod
    def validate_age_group(cls, v: str) -> str:
        """Validate age group."""
        allowed = ["4-6", "7-9", "10-12"]
        if v not in allowed:
            raise ValueError(f"age_group must be one of {allowed}")
        return v

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        """Validate node type."""
        allowed = ["question", "answer", "insight", "root", "branch"]
        if v not in allowed:
            raise ValueError(f"node_type must be one of {allowed}")
        return v


class EmptyBranchRequest(BaseModel):
    """Request schema for generating questions for empty branches."""

    parent_content: str = Field(
        ..., min_length=1, max_length=5000, description="Content of the parent node"
    )
    sibling_contents: List[str] = Field(default_factory=list, description="Content of sibling nodes for context")
    age_group: str = Field(default="7-9", description="Target age group")
    count: int = Field(default=3, ge=1, le=10, description="Number of questions")

    @field_validator("age_group")
    @classmethod
    def validate_age_group(cls, v: str) -> str:
        """Validate age group."""
        allowed = ["4-6", "7-9", "10-12"]
        if v not in allowed:
            raise ValueError(f"age_group must be one of {allowed}")
        return v


class DeepExplorationRequest(BaseModel):
    """Request schema for generating deep exploration questions."""

    node_content: str = Field(
        ..., min_length=1, max_length=5000, description="Content of the node to explore deeply"
    )
    depth: int = Field(default=1, ge=1, le=5, description="Current depth in the tree")
    age_group: str = Field(default="7-9", description="Target age group")
    count: int = Field(default=3, ge=1, le=10, description="Number of questions")

    @field_validator("age_group")
    @classmethod
    def validate_age_group(cls, v: str) -> str:
        """Validate age group."""
        allowed = ["4-6", "7-9", "10-12"]
        if v not in allowed:
            raise ValueError(f"age_group must be one of {allowed}")
        return v


class ConnectionRequest(BaseModel):
    """Request schema for generating connection questions between ideas."""

    source_content: str = Field(
        ..., min_length=1, max_length=5000, description="Content of the source node"
    )
    target_content: str = Field(
        ..., min_length=1, max_length=5000, description="Content of the target node to connect with"
    )
    age_group: str = Field(default="7-9", description="Target age group")
    count: int = Field(default=2, ge=1, le=10, description="Number of questions")

    @field_validator("age_group")
    @classmethod
    def validate_age_group(cls, v: str) -> str:
        """Validate age group."""
        allowed = ["4-6", "7-9", "10-12"]
        if v not in allowed:
            raise ValueError(f"age_group must be one of {allowed}")
        return v


class FollowUpQuestion(BaseModel):
    """A single follow-up question."""

    id: str = Field(..., description="Unique question ID")
    question: str = Field(..., description="The question text")
    category: str = Field(..., description="Question category")
    age_group: str = Field(..., description="Target age group")
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Relevance score")
    context: Optional[str] = Field(None, description="Context for why this question was suggested")
    variations: List[str] = Field(default_factory=list, description="Alternative phrasings")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuestionResponse(BaseModel):
    """Response schema for generated questions."""

    questions: List[FollowUpQuestion] = Field(..., description="Generated questions")
    source_node_content: str = Field(..., description="The node content these questions are based on")
    age_group: str = Field(..., description="Age group used for generation")
    category: Optional[str] = Field(None, description="Category filter applied")


class BatchQuestionResponse(BaseModel):
    """Response schema for batch question generation."""

    results: List[QuestionResponse] = Field(..., description="Question results per node")
    total_questions: int = Field(..., description="Total number of questions generated")
