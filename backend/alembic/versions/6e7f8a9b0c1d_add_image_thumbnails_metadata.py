"""add image thumbnails metadata

Revision ID: 6e7f8a9b0c1d
Revises: 5d6e7f8a9b0c
Create Date: 2026-06-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "6e7f8a9b0c1d"
down_revision: str | None = "5d6e7f8a9b0c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PHOTO_TABLES = ("offer_photos", "item_photos")


def upgrade() -> None:
    for table_name in PHOTO_TABLES:
        op.add_column(table_name, sa.Column("thumbnail_url", sa.String(length=1000), nullable=True))
        op.add_column(table_name, sa.Column("width", sa.Integer(), nullable=True))
        op.add_column(table_name, sa.Column("height", sa.Integer(), nullable=True))
        op.add_column(table_name, sa.Column("thumbnail_width", sa.Integer(), nullable=True))
        op.add_column(table_name, sa.Column("thumbnail_height", sa.Integer(), nullable=True))
        op.add_column(table_name, sa.Column("size_bytes", sa.Integer(), nullable=True))
        op.add_column(table_name, sa.Column("thumbnail_size_bytes", sa.Integer(), nullable=True))


def downgrade() -> None:
    for table_name in PHOTO_TABLES:
        op.drop_column(table_name, "thumbnail_size_bytes")
        op.drop_column(table_name, "size_bytes")
        op.drop_column(table_name, "thumbnail_height")
        op.drop_column(table_name, "thumbnail_width")
        op.drop_column(table_name, "height")
        op.drop_column(table_name, "width")
        op.drop_column(table_name, "thumbnail_url")
