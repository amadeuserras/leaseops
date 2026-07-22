from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import WorkOrder
from leaseops.models.schemas import WorkOrderCreate, WorkOrderStatus, WorkOrderUpdate


async def create_work_order(
    session: AsyncSession, payload: WorkOrderCreate
) -> WorkOrder:
    work_order = WorkOrder(
        tenant_id=payload.tenant_id,
        unit=payload.unit,
        issue=payload.issue,
        status=payload.status,
    )
    session.add(work_order)
    await session.commit()
    await session.refresh(work_order)
    return work_order


async def list_work_orders(
    session: AsyncSession,
    *,
    status: WorkOrderStatus | None = None,
) -> list[WorkOrder]:
    stmt = select(WorkOrder).order_by(WorkOrder.created_at.desc())
    if status is not None:
        stmt = stmt.where(WorkOrder.status == status)
    return list((await session.scalars(stmt)).all())


async def get_work_order(
    session: AsyncSession, work_order_id: UUID
) -> WorkOrder | None:
    return await session.get(WorkOrder, work_order_id)


async def update_work_order(
    session: AsyncSession,
    work_order: WorkOrder,
    payload: WorkOrderUpdate,
) -> WorkOrder:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(work_order, key, value)
    await session.commit()
    await session.refresh(work_order)
    return work_order


async def delete_work_order(session: AsyncSession, work_order: WorkOrder) -> None:
    await session.delete(work_order)
    await session.commit()
