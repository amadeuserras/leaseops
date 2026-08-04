"""drop one-run-per-email unique constraint

Revision ID: a2f8c1d9e4b7
Revises: c9d1e4f7a2b8
Create Date: 2026-08-04 12:52:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "a2f8c1d9e4b7"
down_revision: str | None = "c9d1e4f7a2b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("runs_email_id_key", "runs", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("runs_email_id_key", "runs", ["email_id"])
