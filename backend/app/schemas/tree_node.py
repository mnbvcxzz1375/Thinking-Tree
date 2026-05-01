"""TreeNode schemas with validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List


class TreeNodeBase(BaseModel):
    """Base tree node schema with validation."""

    activity_id: int = Field(..., description="Parent activity ID")
    parent_id: Optional[int] = Field(None, description="Parent node ID")
    content: str = Field(
        ..., min_length=1, max_length=5000, description="Node content"
    )
    node_type: str = Field(default="question", description="Node type")
    position_x: Optional[int] = Field(None, ge=0, description="X position")
    position_y: Optional[int] = Field(None, ge=0, description="Y position")

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        """Validate node type is one of allowed values."""
        allowed = ["question", "answer", "insight", "root", "branch"]
        if v.lower() not in allowed:
            raise ValueError(f"node_type must be one of {allowed}")
        return v.lower()


class TreeNodeCreate(TreeNodeBase):
    """TreeNode creation schema."""

    pass


class TreeNodeCreateInActivity(BaseModel):
    """Schema for creating a node within an activity (activity_id is in the URL)."""

    parent_id: Optional[int] = Field(None, description="Parent node ID")
    content: str = Field(
        ..., min_length=1, max_length=5000, description="Node content"
    )
    node_type: str = Field(default="question", description="Node type")
    position_x: Optional[int] = Field(None, ge=0, description="X position")
    position_y: Optional[int] = Field(None, ge=0, description="Y position")

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        """Validate node type is one of allowed values."""
        allowed = ["question", "answer", "insight", "root", "branch"]
        if v.lower() not in allowed:
            raise ValueError(f"node_type must be one of {allowed}")
        return v.lower()


class TreeNodeUpdate(BaseModel):
    """TreeNode update schema."""

    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    node_type: Optional[str] = None
    position_x: Optional[int] = Field(None, ge=0)
    position_y: Optional[int] = Field(None, ge=0)

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate node type."""
        if v is None:
            return v
        allowed = ["question", "answer", "insight", "root", "branch"]
        if v.lower() not in allowed:
            raise ValueError(f"node_type must be one of {allowed}")
        return v.lower()


class TreeNodeMove(BaseModel):
    """Schema for moving a node to a new parent."""

    new_parent_id: Optional[int] = Field(None, description="New parent node ID (null for root)")


class TreeNodeResponse(TreeNodeBase):
    """TreeNode response schema."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class TreeNodeTreeResponse(TreeNodeResponse):
    """TreeNode with nested children for tree structure."""

    children: List["TreeNodeTreeResponse"] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        from_attributes = True


# Update forward reference
TreeNodeTreeResponse.model_rebuild()
