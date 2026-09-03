"""base inicial vacia

Revision ID: 06d7fb2bda34
Revises:
Create Date: 2026-08-31 20:41:29.577707

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "06d7fb2bda34"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
