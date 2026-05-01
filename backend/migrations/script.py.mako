"""Alembic script template."""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "${rev}"
down_revision = ${down_rev}
branch_labels = ${branch_labels}
depends_on = ${depends_on}


def upgrade() -> None:
    """Upgrade database."""
    pass


def downgrade() -> None:
    """Downgrade database."""
    pass
