"""add telegram identities and links

Revision ID: 7f8a9b0c1d2e
Revises: 6e7f8a9b0c1d
Create Date: 2026-06-29 13:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "7f8a9b0c1d2e"
down_revision: str | None = "6e7f8a9b0c1d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("merged_into_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_merged_into_user_id_users",
        "users",
        "users",
        ["merged_into_user_id"],
        ["id"],
    )

    op.add_column(
        "offers",
        sa.Column("source_idempotency_key", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_offers_source_idempotency_key",
        "offers",
        ["source_idempotency_key"],
    )

    op.create_table(
        "user_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_user_identities_provider_user"),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_identities_user_provider"),
    )

    op.create_table(
        "account_link_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_account_link_tokens_hash"),
    )

    op.create_table(
        "telegram_notification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_type",
            "entity_type",
            "entity_id",
            "user_id",
            name="uq_telegram_notification_events_unique_event",
        ),
    )


def downgrade() -> None:
    op.drop_table("telegram_notification_events")
    op.drop_table("account_link_tokens")
    op.drop_table("user_identities")
    op.drop_constraint("uq_offers_source_idempotency_key", "offers", type_="unique")
    op.drop_column("offers", "source_idempotency_key")
    op.drop_constraint("fk_users_merged_into_user_id_users", "users", type_="foreignkey")
    op.drop_column("users", "merged_at")
    op.drop_column("users", "merged_into_user_id")
