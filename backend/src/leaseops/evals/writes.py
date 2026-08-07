from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.agent.enums import PlanAction
from leaseops.db import outbox as outbox_repo
from leaseops.db import work_orders as work_orders_repo


async def load_performed_actions(
    session: AsyncSession, email_id: UUID
) -> list[PlanAction]:
    outboxes = await outbox_repo.list_outbox_by_email_id(session, email_id)
    work_orders = await work_orders_repo.list_work_orders_by_email_id(
        session, email_id
    )
    return (
        [PlanAction.SEND_REPLY] * len(outboxes)
        + [PlanAction.CREATE_WORK_ORDER] * len(work_orders)
    )
