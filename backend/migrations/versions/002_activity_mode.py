"""Add activity mode fields.

Revision ID: 002_activity_mode
Revises: 001_initial
Create Date: 2026-05-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "002_activity_mode"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add mode and debate-side fields to activities."""
    op.add_column(
        "activities",
        sa.Column("activity_mode", sa.String(length=20), nullable=False, server_default="normal"),
    )
    op.add_column("activities", sa.Column("debate_pro_label", sa.String(length=255), nullable=True))
    op.add_column("activities", sa.Column("debate_con_label", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove mode and debate-side fields from activities."""
    op.drop_column("activities", "debate_con_label")
    op.drop_column("activities", "debate_pro_label")
    op.drop_column("activities", "activity_mode")
