"""Activity service layer for CRUD operations."""
from __future__ import annotations

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate
import logging

logger = logging.getLogger(__name__)


class ActivityService:
    """Service layer for activity CRUD operations."""

    @staticmethod
    def list_activities(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Activity]:
        """List all activities with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, only return active activities

        Returns:
            List of Activity objects
        """
        query = db.query(Activity)
        if active_only:
            query = query.filter(Activity.is_active == True)
        return query.order_by(Activity.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_activity(db: Session, activity_id: int) -> Activity:
        """Get activity by ID.

        Args:
            db: Database session
            activity_id: Activity ID to retrieve

        Returns:
            Activity object

        Raises:
            HTTPException: If activity not found
        """
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity {activity_id} not found",
            )
        return activity

    @staticmethod
    def create_activity(db: Session, activity_data: ActivityCreate) -> Activity:
        """Create a new activity.

        Args:
            db: Database session
            activity_data: Activity creation data

        Returns:
            Created Activity object

        Raises:
            HTTPException: If validation fails
        """
        # Validate difficulty level
        valid_levels = ["easy", "medium", "hard"]
        if activity_data.difficulty_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty_level. Must be one of: {valid_levels}",
            )

        # Validate title is not empty
        if not activity_data.title or not activity_data.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title cannot be empty",
            )

        try:
            db_activity = Activity(**activity_data.model_dump())
            db.add(db_activity)
            db.commit()
            db.refresh(db_activity)
            logger.info(f"Created activity: {db_activity.id} - {db_activity.title}")
            return db_activity
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create activity: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create activity",
            )

    @staticmethod
    def update_activity(
        db: Session,
        activity_id: int,
        activity_data: ActivityUpdate,
    ) -> Activity:
        """Update an existing activity.

        Args:
            db: Database session
            activity_id: Activity ID to update
            activity_data: Activity update data

        Returns:
            Updated Activity object

        Raises:
            HTTPException: If activity not found or validation fails
        """
        db_activity = ActivityService.get_activity(db, activity_id)

        update_data = activity_data.model_dump(exclude_unset=True)

        # Validate difficulty level if provided
        if "difficulty_level" in update_data:
            valid_levels = ["easy", "medium", "hard"]
            if update_data["difficulty_level"] not in valid_levels:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid difficulty_level. Must be one of: {valid_levels}",
                )

        # Validate title if provided
        if "title" in update_data:
            if not update_data["title"] or not update_data["title"].strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Title cannot be empty",
                )

        try:
            for field, value in update_data.items():
                setattr(db_activity, field, value)

            db.add(db_activity)
            db.commit()
            db.refresh(db_activity)
            logger.info(f"Updated activity: {db_activity.id}")
            return db_activity
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update activity {activity_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update activity",
            )

    @staticmethod
    def delete_activity(db: Session, activity_id: int) -> None:
        """Delete an activity.

        Args:
            db: Database session
            activity_id: Activity ID to delete

        Raises:
            HTTPException: If activity not found
        """
        db_activity = ActivityService.get_activity(db, activity_id)

        try:
            db.delete(db_activity)
            db.commit()
            logger.info(f"Deleted activity: {activity_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete activity {activity_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete activity",
            )

    @staticmethod
    def count_activities(db: Session, active_only: bool = False) -> int:
        """Count total activities.

        Args:
            db: Database session
            active_only: If True, only count active activities

        Returns:
            Total count of activities
        """
        query = db.query(Activity)
        if active_only:
            query = query.filter(Activity.is_active == True)
        return query.count()
