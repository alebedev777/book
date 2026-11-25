"""initial

Revision ID: 001
Revises:
Create Date: 2025-11-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "generating_text",
                "generating_images",
                "building_pdf",
                "done",
                "failed",
                name="order_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("theme_id", sa.String(64), nullable=True),
        sa.Column("custom_theme", sa.String(500), nullable=True),
        sa.Column("style_id", sa.String(64), nullable=False),
        sa.Column("child_name", sa.String(100), nullable=False),
        sa.Column("child_age", sa.Integer(), nullable=True),
        sa.Column("locale", sa.String(8), nullable=False, server_default="ru"),
        sa.Column("photo_key", sa.String(512), nullable=True),
        sa.Column("pdf_key", sa.String(512), nullable=True),
        sa.Column("preview_keys", postgresql.JSONB(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("story_json", postgresql.JSONB(), nullable=True),
        sa.Column("character_bible", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("orders")