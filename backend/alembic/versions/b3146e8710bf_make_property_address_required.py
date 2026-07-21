"""make property_address required

Revision ID: b3146e8710bf
Revises: 252c2e344a4f
Create Date: 2026-07-20 12:12:58.884193
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b3146e8710bf"
down_revision: str | None = "252c2e344a4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "tenants", "property_address", existing_type=sa.TEXT(), nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        "tenants", "property_address", existing_type=sa.TEXT(), nullable=True
    )
