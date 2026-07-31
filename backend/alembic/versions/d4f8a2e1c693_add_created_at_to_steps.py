"""add created_at to steps

Revision ID: d4f8a2e1c693
Revises: 96a7ca392c34
Create Date: 2026-07-31 11:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d4f8a2e1c693"
down_revision: str | None = "a8c4e2f91b03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "steps",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("steps", "created_at")
