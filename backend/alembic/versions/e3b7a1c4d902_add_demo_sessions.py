"""add demo_sessions and emails.session_id

Revision ID: e3b7a1c4d902
Revises: a2f8c1d9e4b7
Create Date: 2026-08-11 14:40:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e3b7a1c4d902"
down_revision: str | None = "a2f8c1d9e4b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demo_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Existing emails have no owner; wipe mutable state for NOT NULL session_id.
    op.execute(sa.text("DELETE FROM audit_log"))
    op.execute(sa.text("DELETE FROM steps"))
    op.execute(sa.text("DELETE FROM runs"))
    op.execute(sa.text("DELETE FROM outbox"))
    op.execute(sa.text("DELETE FROM work_orders"))
    op.execute(sa.text("DELETE FROM emails"))

    op.add_column(
        "emails",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_foreign_key(
        "emails_session_id_fkey",
        "emails",
        "demo_sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_emails_session_id", "emails", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_emails_session_id", table_name="emails")
    op.drop_constraint("emails_session_id_fkey", "emails", type_="foreignkey")
    op.drop_column("emails", "session_id")
    op.drop_table("demo_sessions")
