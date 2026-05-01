"""Suggestion router for tree analysis and recommendations.

Mounted at /api/suggestions and provides:
  POST   /suggestions/analyze/{activity_id}  – analyze tree and generate suggestions
  GET    /suggestions/{activity_id}           – list suggestions for activity
  GET    /suggestions/{activity_id}/pending   – get pending suggestion count
  PUT    /suggestions/{suggestion_id}/resolve – accept/reject/dismiss suggestion
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.suggestion import (
    SuggestionAction,
    SuggestionResponse,
    SuggestionStatus,
    SuggestionListResponse,
    TreeAnalysisResult,
)
from app.services.suggestion_service import SuggestionService

router = APIRouter()


@router.post(
    "/analyze/{activity_id}",
    response_model=TreeAnalysisResult,
    summary="Analyze tree and generate suggestions",
)
async def analyze_tree(
    activity_id: int,
    db: Session = Depends(get_db),
) -> TreeAnalysisResult:
    """Analyze the tree structure for an activity and generate smart suggestions.

    This detects:
    - Duplicate/mergeable ideas
    - Complex nodes that should be split
    - Missing thinking directions
    - Tree balance issues
    - Related but unconnected ideas
    """
    svc = SuggestionService(db)
    return svc.analyze_tree(activity_id)


@router.get(
    "/{activity_id}",
    response_model=SuggestionListResponse,
    summary="List suggestions for activity",
)
async def list_suggestions(
    activity_id: int,
    status_filter: Optional[SuggestionStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SuggestionListResponse:
    """Get all suggestions for an activity, optionally filtered by status."""
    svc = SuggestionService(db)
    suggestions = svc.get_suggestions(activity_id, status_filter)
    pending_count = svc.get_pending_count(activity_id)

    return SuggestionListResponse(
        suggestions=suggestions[skip:skip + limit],
        total=len(suggestions),
        pending_count=pending_count,
    )


@router.get(
    "/{activity_id}/pending",
    response_model=int,
    summary="Get pending suggestion count",
)
async def get_pending_count(
    activity_id: int,
    db: Session = Depends(get_db),
) -> int:
    """Get the count of pending suggestions for an activity."""
    svc = SuggestionService(db)
    return svc.get_pending_count(activity_id)


@router.put(
    "/{suggestion_id}/resolve",
    response_model=SuggestionResponse,
    summary="Resolve a suggestion",
)
async def resolve_suggestion(
    suggestion_id: int,
    action: SuggestionAction,
    db: Session = Depends(get_db),
) -> SuggestionResponse:
    """Accept, reject, or dismiss a suggestion.

    Actions:
    - accept: Teacher agrees with the suggestion
    - reject: Teacher disagrees with the suggestion
    - dismiss: Teacher wants to see it later
    """
    svc = SuggestionService(db)
    return svc.resolve_suggestion(suggestion_id, action.action, action.feedback)
