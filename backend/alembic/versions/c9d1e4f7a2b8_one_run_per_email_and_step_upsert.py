"""one run per email and unique step per node

Revision ID: c9d1e4f7a2b8
Revises: f6b2c9d4e815
Create Date: 2026-08-04 12:25:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c9d1e4f7a2b8"
down_revision: str | None = "f6b2c9d4e815"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM runs
            WHERE id NOT IN (
                SELECT DISTINCT ON (email_id) id
                FROM runs
                ORDER BY email_id, started_at DESC
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM steps a
            USING steps b
            WHERE a.run_id = b.run_id
              AND a.node_name = b.node_name
              AND a.created_at < b.created_at
            """
        )
    )
    op.create_unique_constraint("runs_email_id_key", "runs", ["email_id"])
    op.create_unique_constraint(
        "steps_run_id_node_name_key", "steps", ["run_id", "node_name"]
    )


def downgrade() -> None:
    op.drop_constraint("steps_run_id_node_name_key", "steps", type_="unique")
    op.drop_constraint("runs_email_id_key", "runs", type_="unique")
