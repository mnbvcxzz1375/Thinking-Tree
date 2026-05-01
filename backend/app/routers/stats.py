"""Statistics router for activity review and analytics."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.stats import ActivityInsights, ActivityStats, OverviewStats
from app.services.stats_service import StatsService

router = APIRouter()


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    db: Session = Depends(get_db),
) -> OverviewStats:
    """Get overview statistics across all activities.

    Returns aggregate statistics including total activities, nodes,
    speech records, and recent activity summaries.
    """
    service = StatsService(db)
    return service.get_overview_stats()


@router.get("/activities/{activity_id}", response_model=ActivityStats)
async def get_activity_stats(
    activity_id: int,
    db: Session = Depends(get_db),
) -> ActivityStats:
    """Get detailed statistics for a specific activity.

    Returns node counts by type, depth analysis, participation rate,
    time distribution, and most active branches.
    """
    service = StatsService(db)
    return service.get_activity_stats(activity_id)


@router.get("/activities/{activity_id}/insights", response_model=ActivityInsights)
async def get_activity_insights(
    activity_id: int,
    db: Session = Depends(get_db),
) -> ActivityInsights:
    """Get AI-generated insights for an activity.

    Analyzes activity data to produce actionable insights about
    thinking depth, participation, growth trends, and balance.
    """
    service = StatsService(db)
    return service.get_activity_insights(activity_id)
