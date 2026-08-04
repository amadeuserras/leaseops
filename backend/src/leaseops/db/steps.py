from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.agent.step_schemas import NodeName, StepOutput
from leaseops.db.models import Step


async def create_step(
    session: AsyncSession,
    *,
    run_id: UUID,
    node_name: NodeName,
    output: StepOutput,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    cost_usd: float | None = None,
) -> Step:
    step = Step(
        run_id=run_id,
        node_name=node_name,
        output=output.model_dump(mode="json"),
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=Decimal(str(cost_usd)) if cost_usd is not None else None,
    )
    session.add(step)
    await session.commit()
    return step


async def list_steps_for_run(session: AsyncSession, run_id: UUID) -> list[Step]:
    stmt = select(Step).where(Step.run_id == run_id).order_by(Step.created_at)
    return list((await session.scalars(stmt)).all())
