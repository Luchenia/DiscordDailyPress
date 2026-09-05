"""Add nullable soft-delete timestamp to messages."""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260905_02"
down_revision: Union[str, Sequence[str], None] = "20260905_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "messages" not in inspector.get_table_names():
        return

    column_names = {
        column["name"]
        for column in inspector.get_columns("messages")
    }

    if "deleted_at" not in column_names:
        op.add_column(
            "messages",
            sa.Column(
                "deleted_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )


def downgrade() -> None:
    raise NotImplementedError(
        "Removing messages.deleted_at is intentionally unsupported to preserve data."
    )
