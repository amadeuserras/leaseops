"""unique outbox email_id

Revision ID: f3a91c2d8b47
Revises: e7b2c1a94d08
Create Date: 2026-07-28 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "f3a91c2d8b47"
down_revision: str | None = "e7b2c1a94d08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint("outbox_email_id_key", "outbox", ["email_id"])


def downgrade() -> None:
    op.drop_constraint("outbox_email_id_key", "outbox", type_="unique")
