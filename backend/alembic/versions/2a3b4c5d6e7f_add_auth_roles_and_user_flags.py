"""add auth roles and user flags

Revision ID: 2a3b4c5d6e7f
Revises: 1f2a3b4c5d6e
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

import uuid


revision: str = "2a3b4c5d6e7f"
down_revision: str | None = "1f2a3b4c5d6e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "auth_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("login", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=500), nullable=False),
        sa.Column("auth_type", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login", name="uq_auth_accounts_login"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("assigned_by_user_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    roles_table = sa.table(
        "roles",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        roles_table,
        [
            {"id": uuid.uuid4(), "code": "user", "name": "User", "created_at": datetime.now(timezone.utc)},
            {"id": uuid.uuid4(), "code": "editor", "name": "Editor", "created_at": datetime.now(timezone.utc)},
            {"id": uuid.uuid4(), "code": "moderator", "name": "Moderator", "created_at": datetime.now(timezone.utc)},
            {"id": uuid.uuid4(), "code": "admin", "name": "Admin", "created_at": datetime.now(timezone.utc)},
            {"id": uuid.uuid4(), "code": "super_admin", "name": "Super Admin", "created_at": datetime.now(timezone.utc)},
        ],
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("auth_accounts")
    op.drop_column("users", "is_active")
    op.drop_column("users", "phone_verified")
