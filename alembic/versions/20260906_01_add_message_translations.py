"""Add derived message translations table."""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260906_01"
down_revision: Union[str, Sequence[str], None] = "20260905_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "message_translations" in inspector.get_table_names():
        return

    op.create_table(
        "message_translations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("source_language", sa.String(length=10), nullable=False),
        sa.Column("target_language", sa.String(length=10), nullable=False),
        sa.Column("source_content_hash", sa.String(length=64), nullable=False),
        sa.Column("translated_content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["messages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "message_id",
            "target_language",
            "source_content_hash",
            name="uq_message_translation_message_target_hash",
        ),
    )
    op.create_index(
        op.f("ix_message_translations_message_id"),
        "message_translations",
        ["message_id"],
        unique=False,
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Dropping message_translations is intentionally unsupported to preserve data."
    )
