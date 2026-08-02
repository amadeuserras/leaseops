"""drop redundant tokens column from steps

Revision ID: f6b2c9d4e815
Revises: e5a1b8c3d704
Create Date: 2026-08-02 15:25:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f6b2c9d4e815"
down_revision: str | None = "e5a1b8c3d704"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("steps", "tokens")


def downgrade() -> None:
    op.add_column("steps", sa.Column("tokens", sa.Integer(), nullable=True))
