"""Statistics schemas for activity review and analytics."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class NodeCountByType(BaseModel):
    """Node count grouped by type."""

    question: int = Field(default=0, description="Number of question nodes")
    answer: int = Field(default=0, description="Number of answer nodes")
    insight: int = Field(default=0, description="Number of insight nodes")
    root: int = Field(default=0, description="Number of root nodes")
    branch: int = Field(default=0, description="Number of branch nodes")
    total: int = Field(default=0, description="Total number of nodes")


class TimeDistribution(BaseModel):
    """Activity time distribution."""

    date: str = Field(..., description="Date string (YYYY-MM-DD)")
    count: int = Field(default=0, description="Number of nodes created on this date")


class BranchStats(BaseModel):
    """Statistics for a tree branch."""

    node_id: int = Field(..., description="Root node ID of the branch")
    content: str = Field(..., description="Branch root content preview")
    depth: int = Field(default=0, description="Branch depth")
    node_count: int = Field(default=0, description="Total nodes in branch")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


class ActivityStats(BaseModel):
    """Comprehensive statistics for a single activity."""

    activity_id: int = Field(..., description="Activity ID")
    activity_title: str = Field(..., description="Activity title")
    node_counts: NodeCountByType = Field(..., description="Node counts by type")
    max_depth: int = Field(default=0, description="Maximum tree depth")
    avg_depth: float = Field(default=0.0, description="Average node depth")
    total_speech_records: int = Field(default=0, description="Total speech interactions")
    total_reviews: int = Field(default=0, description="Total teacher reviews")
    approved_reviews: int = Field(default=0, description="Approved reviews count")
    participation_rate: float = Field(default=0.0, description="Participation rate (0-1)")
    most_active_branches: list[BranchStats] = Field(
        default_factory=list, description="Top branches by activity"
    )
    time_distribution: list[TimeDistribution] = Field(
        default_factory=list, description="Node creation over time"
    )
    created_at: Optional[datetime] = Field(None, description="Activity creation time")
    last_node_at: Optional[datetime] = Field(None, description="Last node creation time")


class InsightItem(BaseModel):
    """A generated insight about activity progress."""

    category: str = Field(..., description="Insight category: depth, participation, growth, balance")
    title: str = Field(..., description="Short insight title")
    description: str = Field(..., description="Insight description")
    severity: str = Field(default="info", description="Severity: info, success, warning")


class ActivityInsights(BaseModel):
    """Generated insights for an activity."""

    activity_id: int = Field(..., description="Activity ID")
    insights: list[InsightItem] = Field(default_factory=list, description="Generated insights")
    summary: str = Field(default="", description="Overall summary")


class OverviewStats(BaseModel):
    """Overview statistics across all activities."""

    total_activities: int = Field(default=0, description="Total activities")
    active_activities: int = Field(default=0, description="Active activities")
    total_nodes: int = Field(default=0, description="Total tree nodes across all activities")
    total_speech_records: int = Field(default=0, description="Total speech records")
    total_reviews: int = Field(default=0, description="Total teacher reviews")
    avg_nodes_per_activity: float = Field(default=0.0, description="Average nodes per activity")
    recent_activities: list[ActivityStats] = Field(
        default_factory=list, description="Recent activity stats"
    )
