"""add user items and deal status

Revision ID: 1f2a3b4c5d6e
Revises: b9e8d6d4e8a9
Create Date: 2026-05-26 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "1f2a3b4c5d6e"
down_revision: str | None = "b9e8d6d4e8a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "items",
        sa.Column("user_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "items",
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
    )
    op.create_foreign_key(
        "fk_items_user_id_users",
        "items",
        "users",
        ["user_id"],
        ["id"],
    )

    op.add_column(
        "deals",
        sa.Column("status", sa.String(length=50), nullable=False, server_default="new"),
    )
    op.add_column(
        "deals",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE deals SET updated_at = created_at WHERE updated_at IS NULL")
    op.alter_column("deals", "updated_at", nullable=False)
    op.drop_constraint("uq_deals_offer_id", "deals", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("uq_deals_offer_id", "deals", ["offer_id"])
    op.drop_column("deals", "updated_at")
    op.drop_column("deals", "status")

    op.drop_constraint("fk_items_user_id_users", "items", type_="foreignkey")
    op.drop_column("items", "status")
    op.drop_column("items", "user_id")
