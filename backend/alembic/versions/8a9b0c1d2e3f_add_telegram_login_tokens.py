"""add telegram login tokens

Revision ID: 8a9b0c1d2e3f
Revises: 7f8a9b0c1d2e
Create Date: 2026-07-03 00:00:00.000000
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "8a9b0c1d2e3f"
down_revision: str | None = "7f8a9b0c1d2e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "account_link_tokens",
        sa.Column(
            "authenticated_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "account_link_tokens",
        sa.Column(
            "purpose",
            sa.String(length=50),
            nullable=False,
            server_default="account_link",
        ),
    )
    op.create_foreign_key(
        "fk_account_link_tokens_authenticated_user_id_users",
        "account_link_tokens",
        "users",
        ["authenticated_user_id"],
        ["id"],
    )
    op.alter_column("account_link_tokens", "user_id", nullable=True)
    op.alter_column("account_link_tokens", "purpose", server_default=None)


def downgrade() -> None:
    op.execute("DELETE FROM account_link_tokens WHERE purpose = 'telegram_login'")
    op.alter_column("account_link_tokens", "user_id", nullable=False)
    op.drop_constraint(
        "fk_account_link_tokens_authenticated_user_id_users",
        "account_link_tokens",
        type_="foreignkey",
    )
    op.drop_column("account_link_tokens", "purpose")
    op.drop_column("account_link_tokens", "authenticated_user_id")
