"""add unique email_id to work_orders

Revision ID: a8c4e2f91b03
Revises: f3a91c2d8b47
Create Date: 2026-07-28 12:15:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a8c4e2f91b03"
down_revision: str | None = "f3a91c2d8b47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("DELETE FROM work_orders"))
    op.add_column(
        "work_orders",
        sa.Column("email_id", sa.UUID(), nullable=False),
    )
    op.create_foreign_key(
        "work_orders_email_id_fkey",
        "work_orders",
        "emails",
        ["email_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint("work_orders_email_id_key", "work_orders", ["email_id"])


def downgrade() -> None:
    op.drop_constraint("work_orders_email_id_key", "work_orders", type_="unique")
    op.drop_constraint("work_orders_email_id_fkey", "work_orders", type_="foreignkey")
    op.drop_column("work_orders", "email_id")
