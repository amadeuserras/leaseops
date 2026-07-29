from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import Run
from leaseops.models.enums import RunStatus


def _utcnow() -> datetime:
    return datetime.now(UTC)


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
) -> list[Run]:
    stmt = select(Run).order_by(Run.started_at.desc())
    if status is not None:
        stmt = stmt.where(Run.status == status)
    return list((await session.scalars(stmt)).all())


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
