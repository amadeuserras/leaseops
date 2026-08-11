from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import Email, Outbox, Run, Step, WorkOrder
from leaseops.models.enums import EmailStatus, RunStatus


def _utcnow() -> datetime:
    return datetime.now(UTC)


class RunAggregates(TypedDict):
    tokens: int
    cost: float
    elapsed: float
    step_count: int


def run_aggregates(run: Run, steps: list[Step]) -> RunAggregates:
    tokens = sum((s.input_tokens or 0) + (s.output_tokens or 0) for s in steps)
    cost = sum(float(s.cost_usd or 0) for s in steps)
    end = run.ended_at or (steps[-1].created_at if steps else run.started_at)
    return {
        "tokens": tokens,
        "cost": cost,
        "elapsed": (end - run.started_at).total_seconds(),
        "step_count": len(steps),
    }


async def create_run(session: AsyncSession, email_id: UUID) -> Run:
    run = Run(email_id=email_id, status=RunStatus.RUNNING)
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def get_run(session: AsyncSession, run_id: UUID) -> Run | None:
    return await session.get(Run, run_id)


async def list_runs(
    session: AsyncSession,
    *,
    status: RunStatus | None = None,
    session_id: UUID | None = None,
) -> list[Run]:
    stmt = select(Run).order_by(Run.started_at.desc())
    if session_id is not None:
        stmt = stmt.join(Email, Email.id == Run.email_id).where(
            Email.session_id == session_id
        )
    if status is not None:
        stmt = stmt.where(Run.status == status)
    return list((await session.scalars(stmt)).all())


async def get_latest_run(
    session: AsyncSession, *, session_id: UUID | None = None
) -> Run | None:
    stmt = select(Run).order_by(Run.started_at.desc()).limit(1)
    if session_id is not None:
        stmt = stmt.join(Email, Email.id == Run.email_id).where(
            Email.session_id == session_id
        )
    return (await session.scalars(stmt)).first()


async def get_run_by_email_id(session: AsyncSession, email_id: UUID) -> Run | None:
    return (
        await session.scalars(select(Run).where(Run.email_id == email_id))
    ).one_or_none()


async def get_run_for_session(
    session: AsyncSession, run_id: UUID, *, session_id: UUID
) -> Run | None:
    return (
        await session.scalars(
            select(Run)
            .join(Email, Email.id == Run.email_id)
            .where(Run.id == run_id, Email.session_id == session_id)
        )
    ).one_or_none()


async def wipe_run(session: AsyncSession, email_id: UUID) -> UUID | None:
    run = await get_run_by_email_id(session, email_id)
    run_id = run.id if run is not None else None
    await session.execute(delete(Outbox).where(Outbox.email_id == email_id))
    await session.execute(delete(WorkOrder).where(WorkOrder.email_id == email_id))
    await session.execute(delete(Run).where(Run.email_id == email_id))
    email = await session.get(Email, email_id)
    if email is not None:
        email.status = EmailStatus.PENDING
    await session.commit()
    return run_id


async def get_agent_last_ran_at(
    session: AsyncSession, *, session_id: UUID | None = None
) -> datetime | None:
    stmt = select(func.max(Run.ended_at)).select_from(Run)
    if session_id is not None:
        stmt = stmt.join(Email, Email.id == Run.email_id).where(
            Email.session_id == session_id
        )
    return await session.scalar(stmt)


async def set_run_status(
    session: AsyncSession,
    run: Run,
    status: RunStatus,
    *,
    ended: bool = False,
) -> Run:
    run.status = status
    if ended:
        run.ended_at = _utcnow()
    await session.commit()
    await session.refresh(run)
    return run
