"""Data export/import service."""
import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.activity import Activity
from app.models.tree_node import TreeNode
from app.models.speech_record import SpeechRecord
from app.models.teacher_review import TeacherReview
from app.schemas.export import ExportOptions, ExportData, ImportResult


class DataService:
    """Service for data export and import operations."""

    @staticmethod
    def export_data(db: Session, options: ExportOptions) -> ExportData:
        """Export data from database based on options."""
        export = ExportData(
            version="1.0",
            exported_at=datetime.utcnow(),
            metadata={
                "options": options.model_dump(),
                "exported_by": "system",
            },
        )

        # Export activities
        if options.include_activities:
            query = db.query(Activity)
            if options.activity_ids:
                query = query.filter(Activity.id.in_(options.activity_ids))
            activities = query.all()
            export.activities = [
                {
                    "id": a.id,
                    "title": a.title,
                    "description": a.description,
                    "instructions": a.instructions,
                    "difficulty_level": a.difficulty_level,
                    "age_group": a.age_group,
                    "is_active": a.is_active,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "updated_at": a.updated_at.isoformat() if a.updated_at else None,
                }
                for a in activities
            ]

        # Export tree nodes
        if options.include_tree_nodes:
            query = db.query(TreeNode)
            if options.activity_ids:
                query = query.filter(TreeNode.activity_id.in_(options.activity_ids))
            nodes = query.all()
            export.tree_nodes = [
                {
                    "id": n.id,
                    "activity_id": n.activity_id,
                    "parent_id": n.parent_id,
                    "content": n.content,
                    "node_type": n.node_type,
                    "position_x": n.position_x,
                    "position_y": n.position_y,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                    "updated_at": n.updated_at.isoformat() if n.updated_at else None,
                }
                for n in nodes
            ]

        # Export speech records
        if options.include_speech_records:
            query = db.query(SpeechRecord)
            if options.activity_ids:
                query = query.filter(
                    SpeechRecord.activity_id.in_(options.activity_ids)
                )
            records = query.all()
            export.speech_records = [
                {
                    "id": r.id,
                    "activity_id": r.activity_id,
                    "tree_node_id": r.tree_node_id,
                    "user_input": r.user_input,
                    "ai_response": r.ai_response,
                    "audio_url": r.audio_url,
                    "duration_seconds": r.duration_seconds,
                    "confidence_score": r.confidence_score,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]

        # Export teacher reviews
        if options.include_teacher_reviews:
            query = db.query(TeacherReview)
            if options.activity_ids:
                # Filter by tree nodes that belong to specified activities
                node_ids = (
                    db.query(TreeNode.id)
                    .filter(TreeNode.activity_id.in_(options.activity_ids))
                    .subquery()
                )
                query = query.filter(TeacherReview.tree_node_id.in_(node_ids))
            reviews = query.all()
            export.teacher_reviews = [
                {
                    "id": r.id,
                    "tree_node_id": r.tree_node_id,
                    "teacher_name": r.teacher_name,
                    "feedback": r.feedback,
                    "rating": r.rating,
                    "is_approved": r.is_approved,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in reviews
            ]

        return export

    @staticmethod
    def import_data(db: Session, data: ExportData) -> ImportResult:
        """Import data into database."""
        result = ImportResult(success=True)

        # Track ID mappings for relationships
        activity_id_map = {}
        node_id_map = {}

        try:
            # Import activities
            for activity_data in data.activities:
                old_id = activity_data.pop("id", None)
                # Remove timestamps (will be auto-generated)
                activity_data.pop("created_at", None)
                activity_data.pop("updated_at", None)

                activity = Activity(**activity_data)
                db.add(activity)
                db.flush()  # Get the new ID
                if old_id is not None:
                    activity_id_map[old_id] = activity.id
                result.activities_imported += 1

            # Import tree nodes
            for node_data in data.tree_nodes:
                old_id = node_data.pop("id", None)
                node_data.pop("created_at", None)
                node_data.pop("updated_at", None)

                # Map activity_id
                old_activity_id = node_data.get("activity_id")
                if old_activity_id in activity_id_map:
                    node_data["activity_id"] = activity_id_map[old_activity_id]

                # Map parent_id
                old_parent_id = node_data.get("parent_id")
                if old_parent_id and old_parent_id in node_id_map:
                    node_data["parent_id"] = node_id_map[old_parent_id]
                elif old_parent_id:
                    node_data["parent_id"] = None
                    result.warnings.append(
                        f"Parent node {old_parent_id} not found, set to root"
                    )

                node = TreeNode(**node_data)
                db.add(node)
                db.flush()
                if old_id is not None:
                    node_id_map[old_id] = node.id
                result.tree_nodes_imported += 1

            # Import speech records
            for record_data in data.speech_records:
                record_data.pop("id", None)
                record_data.pop("created_at", None)

                # Map IDs
                old_activity_id = record_data.get("activity_id")
                if old_activity_id in activity_id_map:
                    record_data["activity_id"] = activity_id_map[old_activity_id]

                old_node_id = record_data.get("tree_node_id")
                if old_node_id and old_node_id in node_id_map:
                    record_data["tree_node_id"] = node_id_map[old_node_id]
                elif old_node_id:
                    record_data["tree_node_id"] = None

                record = SpeechRecord(**record_data)
                db.add(record)
                result.speech_records_imported += 1

            # Import teacher reviews
            for review_data in data.teacher_reviews:
                review_data.pop("id", None)
                review_data.pop("created_at", None)
                review_data.pop("updated_at", None)

                old_node_id = review_data.get("tree_node_id")
                if old_node_id and old_node_id in node_id_map:
                    review_data["tree_node_id"] = node_id_map[old_node_id]
                else:
                    result.warnings.append(
                        f"Tree node {old_node_id} not found for review, skipping"
                    )
                    continue

                review = TeacherReview(**review_data)
                db.add(review)
                result.teacher_reviews_imported += 1

            db.commit()

        except Exception as e:
            db.rollback()
            result.success = False
            result.errors.append(str(e))

        return result

    @staticmethod
    def export_to_json(export_data: ExportData) -> str:
        """Convert export data to JSON string."""
        return export_data.model_dump_json(indent=2)

    @staticmethod
    def import_from_json(json_str: str) -> ExportData:
        """Parse JSON string to export data."""
        return ExportData.model_validate_json(json_str)
