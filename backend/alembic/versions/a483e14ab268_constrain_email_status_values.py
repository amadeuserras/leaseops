"""constrain email status values

Revision ID: a483e14ab268
Revises: 38eaa9325770
Create Date: 2026-07-22 10:40:40.358977
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "a483e14ab268"
down_revision: str | None = "38eaa9325770"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "emails_status_check",
        "emails",
        "status IN ('pending', 'processed', 'escalated')",
    )


def downgrade() -> None:
    op.drop_constraint("emails_status_check", "emails", type_="check")
