"""make work_order unit nullable

Revision ID: d1e4a9c2b7f0
Revises: 96a7ca392c34
Create Date: 2026-07-26 17:34:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d1e4a9c2b7f0"
down_revision: str | None = "96a7ca392c34"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "work_orders",
        "unit",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "work_orders",
        "unit",
        existing_type=sa.Text(),
        nullable=False,
    )
