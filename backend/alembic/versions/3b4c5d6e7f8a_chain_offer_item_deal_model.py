"""chain offer item deal model

Revision ID: 3b4c5d6e7f8a
Revises: 2a3b4c5d6e7f
Create Date: 2026-06-28 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "3b4c5d6e7f8a"
down_revision: str | None = "2a3b4c5d6e7f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "offers",
        sa.Column("visibility_status", sa.String(length=50), nullable=False, server_default="normal"),
    )
    op.add_column(
        "offers",
        sa.Column("sort_priority", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "items",
        sa.Column("source_offer_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "items",
        sa.Column("sequence_number", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_items_source_offer_id_offers",
        "items",
        "offers",
        ["source_offer_id"],
        ["id"],
    )

    # Safe status mapping for the new request-centric model:
    # published/approved/moderation meant "admin processed" in the marketplace model,
    # not "selected into chain"; selected is assigned only when a linked deal exists.
    op.execute("UPDATE offers SET status = 'reviewed' WHERE status IN ('published', 'approved', 'moderation')")
    op.execute("UPDATE offers SET status = 'hidden', visibility_status = 'hidden' WHERE status = 'archived'")
    op.execute(
        """
        UPDATE offers
        SET status = 'selected'
        WHERE id IN (
            SELECT DISTINCT offer_id
            FROM deals
            WHERE offer_id IS NOT NULL AND status = 'completed'
        )
        """
    )

    op.execute("UPDATE items SET status = 'past' WHERE is_current = false AND status = 'active'")
    op.execute("UPDATE items SET status = 'current' WHERE is_current = true")
    op.execute(
        """
        UPDATE items
        SET source_offer_id = (
            SELECT d.offer_id
            FROM deals d
            WHERE d.received_item_id = items.id
            LIMIT 1
        )
        WHERE source_offer_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE items
        SET sequence_number = (
            SELECT d.step_number
            FROM deals d
            WHERE d.received_item_id = items.id
            LIMIT 1
        )
        WHERE sequence_number IS NULL
        """
    )
    op.execute(
        """
        UPDATE items
        SET sequence_number = 0
        WHERE sequence_number IS NULL
          AND id IN (SELECT given_item_id FROM deals WHERE step_number = 1)
        """
    )


def downgrade() -> None:
    op.drop_constraint("fk_items_source_offer_id_offers", "items", type_="foreignkey")
    op.drop_column("items", "sequence_number")
    op.drop_column("items", "source_offer_id")
    op.drop_column("offers", "sort_priority")
    op.drop_column("offers", "visibility_status")
