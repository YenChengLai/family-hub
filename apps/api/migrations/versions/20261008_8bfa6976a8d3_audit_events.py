"""audit events

Revision ID: 8bfa6976a8d3
Revises: b4c90ed72879
Create Date: 2026-10-08 07:56:23.653545
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8bfa6976a8d3"
down_revision: str | None = "b4c90ed72879"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("household_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
        schema="platform",
    )
    op.create_index(
        "ix_audit_events_household_occurred",
        "audit_events",
        ["household_id", "occurred_at"],
        unique=False,
        schema="platform",
    )
    # AUDIT-2: the log is append-only, enforced by the database itself.
    op.execute(
        """
        CREATE FUNCTION platform.audit_events_append_only() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'platform.audit_events is append-only';
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_append_only
        BEFORE UPDATE OR DELETE ON platform.audit_events
        FOR EACH ROW EXECUTE FUNCTION platform.audit_events_append_only()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER audit_events_append_only ON platform.audit_events")
    op.execute("DROP FUNCTION platform.audit_events_append_only()")
    op.drop_index(
        "ix_audit_events_household_occurred", table_name="audit_events", schema="platform"
    )
    op.drop_table("audit_events", schema="platform")
