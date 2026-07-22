"""split property_address into address and unit

Revision ID: c0f78e2f265d
Revises: a483e14ab268
Create Date: 2026-07-22 11:45:57.414180
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c0f78e2f265d"
down_revision: str | None = "a483e14ab268"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("address", sa.Text(), nullable=True))
    op.add_column("tenants", sa.Column("unit", sa.Text(), nullable=True))
    op.execute(sa.text("UPDATE tenants SET address = property_address"))
    op.alter_column("tenants", "address", existing_type=sa.Text(), nullable=False)
    op.drop_column("tenants", "property_address")


def downgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("property_address", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.execute(sa.text("UPDATE tenants SET property_address = address"))
    op.alter_column(
        "tenants", "property_address", existing_type=sa.Text(), nullable=False
    )
    op.drop_column("tenants", "unit")
    op.drop_column("tenants", "address")
