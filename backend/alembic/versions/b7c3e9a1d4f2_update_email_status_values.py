"""update email status values

Revision ID: b7c3e9a1d4f2
Revises: d4f8a2e1c693
Create Date: 2026-08-01 17:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "b7c3e9a1d4f2"
down_revision: str | None = "d4f8a2e1c693"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("emails_status_check", "emails", type_="check")
    op.execute(
        "UPDATE emails SET status = 'awaiting_approval' WHERE status = 'escalated'"
    )
    op.create_check_constraint(
        "emails_status_check",
        "emails",
        "status IN ('pending', 'processing', 'awaiting_approval', 'processed')",
    )


def downgrade() -> None:
    op.drop_constraint("emails_status_check", "emails", type_="check")
    op.execute(
        "UPDATE emails SET status = 'escalated' WHERE status = 'awaiting_approval'"
    )
    op.execute("UPDATE emails SET status = 'pending' WHERE status = 'processing'")
    op.create_check_constraint(
        "emails_status_check",
        "emails",
        "status IN ('pending', 'processed', 'escalated')",
    )
