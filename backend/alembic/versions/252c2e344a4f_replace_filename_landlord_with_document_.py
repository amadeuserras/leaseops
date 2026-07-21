"""replace filename landlord with document_id

Revision ID: 252c2e344a4f
Revises: 511ea92deb2d
Create Date: 2026-07-20 12:05:42.128854
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "252c2e344a4f"
down_revision: str | None = "511ea92deb2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("document_id", sa.UUID(), nullable=False))
    op.drop_column("tenants", "landlord_name")
    op.drop_column("tenants", "filename")


def downgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("filename", sa.TEXT(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "tenants",
        sa.Column("landlord_name", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.drop_column("tenants", "document_id")
