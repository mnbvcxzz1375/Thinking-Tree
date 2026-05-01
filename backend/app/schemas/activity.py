"""Activity schemas with validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class ActivityBase(BaseModel):
    """Base activity schema with validation."""

    title: str = Field(
        ..., min_length=1, max_length=255, description="Activity title"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Activity description"
    )
    instructions: Optional[str] = Field(
        None, max_length=5000, description="Activity instructions"
    )
    difficulty_level: str = Field(
        default="medium", description="Difficulty level"
    )
    age_group: Optional[str] = Field(None, description="Target age group")
    is_active: bool = Field(default=True, description="Whether activity is active")

    @field_validator("difficulty_level")
    @classmethod
    def validate_difficulty_level(cls, v: str) -> str:
        """Validate difficulty level is one of allowed values."""
        allowed = ["easy", "medium", "hard"]
        if v.lower() not in allowed:
            raise ValueError(f"difficulty_level must be one of {allowed}")
        return v.lower()

    @field_validator("age_group")
    @classmethod
    def validate_age_group(cls, v: Optional[str]) -> Optional[str]:
        """Validate age group format."""
        if v is None:
            return v
        allowed = ["3-5", "5-7", "7-9", "9-12", "all"]
        if v not in allowed:
            raise ValueError(f"age_group must be one of {allowed}")
        return v


class ActivityCreate(ActivityBase):
    """Activity creation schema."""

    pass


class ActivityUpdate(BaseModel):
    """Activity update schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    instructions: Optional[str] = Field(None, max_length=5000)
    difficulty_level: Optional[str] = None
    age_group: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("difficulty_level")
    @classmethod
    def validate_difficulty_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate difficulty level."""
        if v is None:
            return v
        allowed = ["easy", "medium", "hard"]
        if v.lower() not in allowed:
            raise ValueError(f"difficulty_level must be one of {allowed}")
        return v.lower()

    @field_validator("age_group")
    @classmethod
    def validate_age_group(cls, v: Optional[str]) -> Optional[str]:
        """Validate age group format."""
        if v is None:
            return v
        allowed = ["3-5", "5-7", "7-9", "9-12", "all"]
        if v not in allowed:
            raise ValueError(f"age_group must be one of {allowed}")
        return v


class ActivityResponse(ActivityBase):
    """Activity response schema."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
