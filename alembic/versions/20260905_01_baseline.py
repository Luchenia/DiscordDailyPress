"""Establish Alembic tracking for the existing ORM-managed schema."""

from typing import Sequence
from typing import Union

from alembic import op


revision: str = "20260905_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing deployments create the baseline schema through Base.metadata.create_all.
    # This revision only begins Alembic version tracking and preserves that schema.
    pass


def downgrade() -> None:
    # Removing version tracking does not alter application data or schema.
    pass
