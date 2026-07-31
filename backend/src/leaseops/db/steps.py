from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import Step


async def create_step(
    session: AsyncSession,
    *,
    run_id: UUID,
    node_name: str,
    output: Any,
    tokens: int | None = None,
    cost_usd: float | None = None,
) -> Step:
    step = Step(
        run_id=run_id,
        node_name=node_name,
        output=output,
        tokens=tokens,
        cost_usd=Decimal(str(cost_usd)) if cost_usd is not None else None,
    )
    session.add(step)
    await session.commit()
    return step
