"""Activities router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from app.services.activity_service import ActivityService

router = APIRouter()


@router.get("", response_model=list[ActivityResponse])
async def list_activities(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    active_only: bool = Query(False, description="Filter active activities only"),
    db: Session = Depends(get_db),
) -> list[ActivityResponse]:
    """List all activities.

    Returns a paginated list of activities with optional active-only filter.
    """
    return ActivityService.list_activities(db, skip=skip, limit=limit, active_only=active_only)


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
) -> ActivityResponse:
    """Get activity by ID.

    Returns detailed information about a specific activity.
    """
    return ActivityService.get_activity(db, activity_id)


@router.post("", response_model=ActivityResponse, status_code=201)
async def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db),
) -> ActivityResponse:
    """Create a new activity.

    Creates a new thinking tree activity with the provided details.
    """
    return ActivityService.create_activity(db, activity)


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: int,
    activity: ActivityUpdate,
    db: Session = Depends(get_db),
) -> ActivityResponse:
    """Update an activity.

    Updates an existing activity with the provided details.
    Only provided fields will be updated.
    """
    return ActivityService.update_activity(db, activity_id, activity)


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """Delete an activity.

    Permanently removes an activity and all associated data.
    """
    ActivityService.delete_activity(db, activity_id)
    return Response(status_code=204)
