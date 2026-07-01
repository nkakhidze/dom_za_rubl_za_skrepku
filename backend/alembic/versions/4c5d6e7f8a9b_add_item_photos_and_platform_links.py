"""add item photos and platform links

Revision ID: 4c5d6e7f8a9b
Revises: 3b4c5d6e7f8a
Create Date: 2026-06-28 00:00:00.000000
"""

from collections.abc import Sequence
import uuid

import sqlalchemy as sa
from alembic import op


revision: str = "4c5d6e7f8a9b"
down_revision: str | None = "3b4c5d6e7f8a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("items", sa.Column("vk_url", sa.String(length=1000), nullable=True))
    op.add_column("items", sa.Column("tiktok_url", sa.String(length=1000), nullable=True))
    op.add_column("items", sa.Column("youtube_url", sa.String(length=1000), nullable=True))
    op.add_column("items", sa.Column("dzen_url", sa.String(length=1000), nullable=True))
    op.add_column("items", sa.Column("rutube_url", sa.String(length=1000), nullable=True))
    op.add_column("items", sa.Column("instagram_url", sa.String(length=1000), nullable=True))

    op.create_table(
        "item_photos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("item_id", sa.UUID(), nullable=False),
        sa.Column("photo_url", sa.String(length=1000), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    connection = op.get_bind()
    items = connection.execute(
        sa.text("SELECT id, photo_url, created_at FROM items WHERE photo_url IS NOT NULL AND photo_url != ''")
    ).mappings()

    for item in items:
        connection.execute(
            sa.text(
                """
                INSERT INTO item_photos (id, item_id, photo_url, sort_order, created_at)
                VALUES (:id, :item_id, :photo_url, 0, :created_at)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "item_id": item["id"],
                "photo_url": item["photo_url"],
                "created_at": item["created_at"],
            },
        )


def downgrade() -> None:
    op.drop_table("item_photos")
    op.drop_column("items", "instagram_url")
    op.drop_column("items", "rutube_url")
    op.drop_column("items", "dzen_url")
    op.drop_column("items", "youtube_url")
    op.drop_column("items", "tiktok_url")
    op.drop_column("items", "vk_url")
