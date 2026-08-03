from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.agent.state import AgentState, PlanAction
from leaseops.agent.step_schemas import ExecuteOutput
from leaseops.api.schemas import OutboxCreate, WorkOrderCreate
from leaseops.db import emails as emails_repo
from leaseops.db import outbox as outbox_repo
from leaseops.db import tenants as tenants_repo
from leaseops.db import work_orders as work_orders_repo
from leaseops.db.models import Tenant
from leaseops.db.session import SessionLocal
from leaseops.models.enums import EmailStatus, OutboxStatus, WorkOrderStatus


async def _resolve_tenant(session: AsyncSession, state: AgentState) -> Tenant:
    tenant = await tenants_repo.get_tenant_by_email(session, state.sender)
    if tenant is None:
        raise RuntimeError("create_work_order requires a known tenant")
    return tenant


async def _send_reply(session: AsyncSession, state: AgentState) -> None:
    if state.draft is None:
        raise RuntimeError("send_reply requires a draft")
    await outbox_repo.create_outbox_entry(
        session,
        OutboxCreate(
            email_id=state.email_id,
            draft_text=state.draft,
            status=OutboxStatus.APPROVED,
        ),
    )


async def _create_work_order(session: AsyncSession, state: AgentState) -> None:
    tenant = await _resolve_tenant(session, state)
    issue = state.issue_summary or state.subject
    await work_orders_repo.create_work_order(
        session,
        WorkOrderCreate(
            email_id=state.email_id,
            tenant_id=tenant.id,
            issue=issue,
            status=WorkOrderStatus.OPEN,
        ),
    )


async def execute(state: AgentState) -> ExecuteOutput:
    actions_taken: list[PlanAction] = []
    async with SessionLocal() as session:
        for action in state.actions:
            if action == PlanAction.SEND_REPLY:
                await _send_reply(session, state)
            elif action == PlanAction.CREATE_WORK_ORDER:
                await _create_work_order(session, state)
            else:
                raise RuntimeError(f"unknown action: {action}")
            actions_taken.append(action)
        await emails_repo.set_email_status(
            session, state.email_id, EmailStatus.PROCESSED
        )
    return ExecuteOutput(actions_taken=actions_taken)
