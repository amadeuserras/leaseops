"""add step cost breakdown columns

Revision ID: e5a1b8c3d704
Revises: b7c3e9a1d4f2
Create Date: 2026-08-02 15:20:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e5a1b8c3d704"
down_revision: str | None = "b7c3e9a1d4f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("steps", sa.Column("model", sa.Text(), nullable=True))
    op.add_column("steps", sa.Column("input_tokens", sa.Integer(), nullable=True))
    op.add_column("steps", sa.Column("output_tokens", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("steps", "output_tokens")
    op.drop_column("steps", "input_tokens")
    op.drop_column("steps", "model")
