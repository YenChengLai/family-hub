"""platform identity and households

Revision ID: b4c90ed72879
Revises:
Create Date: 2026-10-08 06:27:32.099230
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b4c90ed72879"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS platform")
    op.create_table(
        "households",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_households")),
        schema="platform",
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        schema="platform",
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("household_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('owner', 'adult', 'child')", name=op.f("ck_memberships_role_valid")
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["platform.households.id"],
            name=op.f("fk_memberships_household_id_households"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["platform.users.id"],
            name=op.f("fk_memberships_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memberships")),
        sa.UniqueConstraint("household_id", "user_id", name=op.f("uq_memberships_household_id")),
        schema="platform",
    )
    op.create_index(
        op.f("ix_platform_memberships_household_id"),
        "memberships",
        ["household_id"],
        unique=False,
        schema="platform",
    )
    op.create_index(
        op.f("ix_platform_memberships_user_id"),
        "memberships",
        ["user_id"],
        unique=False,
        schema="platform",
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["platform.users.id"],
            name=op.f("fk_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_sessions_token_hash")),
        schema="platform",
    )
    op.create_index(
        op.f("ix_platform_sessions_user_id"),
        "sessions",
        ["user_id"],
        unique=False,
        schema="platform",
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_platform_sessions_user_id"), table_name="sessions", schema="platform")
    op.drop_table("sessions", schema="platform")
    op.drop_index(
        op.f("ix_platform_memberships_user_id"), table_name="memberships", schema="platform"
    )
    op.drop_index(
        op.f("ix_platform_memberships_household_id"), table_name="memberships", schema="platform"
    )
    op.drop_table("memberships", schema="platform")
    op.drop_table("users", schema="platform")
    op.drop_table("households", schema="platform")
    op.execute("DROP SCHEMA IF EXISTS platform")
