from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import Step


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


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
        output=_jsonable(output) if output is not None else None,
        tokens=tokens,
        cost_usd=Decimal(str(cost_usd)) if cost_usd is not None else None,
    )
    session.add(step)
    await session.commit()
    return step


async def list_steps_for_run(session: AsyncSession, run_id: UUID) -> list[Step]:
    stmt = select(Step).where(Step.run_id == run_id).order_by(Step.created_at)
    return list((await session.scalars(stmt)).all())
