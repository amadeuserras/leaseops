"""drop unit from work_orders

Revision ID: e7b2c1a94d08
Revises: d1e4a9c2b7f0
Create Date: 2026-07-27 17:48:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e7b2c1a94d08"
down_revision: str | None = "d1e4a9c2b7f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("work_orders", "unit")


def downgrade() -> None:
    op.add_column(
        "work_orders",
        sa.Column("unit", sa.Text(), nullable=True),
    )
