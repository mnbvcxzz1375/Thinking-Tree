"""Initial migration - create all tables.

Revision ID: 001_initial
Revises: 
Create Date: 2026-05-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    # Create activities table
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("difficulty_level", sa.String(50), nullable=False),
        sa.Column("age_group", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_activity_is_active", "activities", ["is_active"])
    op.create_index("idx_activity_created_at", "activities", ["created_at"])
    op.create_index("ix_activities_title", "activities", ["title"])

    # Create tree_nodes table
    op.create_table(
        "tree_nodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("node_type", sa.String(50), nullable=False),
        sa.Column("position_x", sa.Integer(), nullable=True),
        sa.Column("position_y", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["tree_nodes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_tree_node_activity_id", "tree_nodes", ["activity_id"])
    op.create_index("idx_tree_node_parent_id", "tree_nodes", ["parent_id"])
    op.create_index("idx_tree_node_created_at", "tree_nodes", ["created_at"])

    # Create speech_records table
    op.create_table(
        "speech_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("tree_node_id", sa.Integer(), nullable=True),
        sa.Column("user_input", sa.Text(), nullable=False),
        sa.Column("ai_response", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.String(500), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"]),
        sa.ForeignKeyConstraint(["tree_node_id"], ["tree_nodes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_speech_record_activity_id", "speech_records", ["activity_id"])
    op.create_index("idx_speech_record_tree_node_id", "speech_records", ["tree_node_id"])
    op.create_index("idx_speech_record_created_at", "speech_records", ["created_at"])

    # Create teacher_reviews table
    op.create_table(
        "teacher_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tree_node_id", sa.Integer(), nullable=False),
        sa.Column("teacher_name", sa.String(255), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("is_approved", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tree_node_id"], ["tree_nodes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_teacher_review_tree_node_id", "teacher_reviews", ["tree_node_id"])
    op.create_index("idx_teacher_review_is_approved", "teacher_reviews", ["is_approved"])
    op.create_index("idx_teacher_review_created_at", "teacher_reviews", ["created_at"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("idx_teacher_review_created_at", table_name="teacher_reviews")
    op.drop_index("idx_teacher_review_is_approved", table_name="teacher_reviews")
    op.drop_index("idx_teacher_review_tree_node_id", table_name="teacher_reviews")
    op.drop_table("teacher_reviews")

    op.drop_index("idx_speech_record_created_at", table_name="speech_records")
    op.drop_index("idx_speech_record_tree_node_id", table_name="speech_records")
    op.drop_index("idx_speech_record_activity_id", table_name="speech_records")
    op.drop_table("speech_records")

    op.drop_index("idx_tree_node_created_at", table_name="tree_nodes")
    op.drop_index("idx_tree_node_parent_id", table_name="tree_nodes")
    op.drop_index("idx_tree_node_activity_id", table_name="tree_nodes")
    op.drop_table("tree_nodes")

    op.drop_index("idx_activity_created_at", table_name="activities")
    op.drop_index("idx_activity_is_active", table_name="activities")
    op.drop_index("ix_activities_title", table_name="activities")
    op.drop_table("activities")
