from __future__ import annotations

from uuid import UUID

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from leaseops.clients import leaseclear
from leaseops.clients.leaseclear import LeaseClearError
from leaseops.db import emails as repo
from leaseops.db import outbox as outbox_repo
from leaseops.db import tenants as tenants_repo
from leaseops.db import work_orders as work_orders_repo
from leaseops.db.session import SessionLocal
from leaseops.models.schemas import (
    LeaseQAResponse,
    OutboxCreate,
    OutboxResponse,
    TenantResponse,
    WorkOrderCreate,
    WorkOrderListResponse,
    WorkOrderResponse,
    WorkOrderStatus,
    WorkOrderUpdate,
)

mcp = FastMCP("leaseops")


@mcp.tool()
async def tenant_lookup(email: str) -> TenantResponse:
    """Resolve a sender email to tenant, unit, and LeaseClear document id."""
    async with SessionLocal() as session:
        tenant = await tenants_repo.get_tenant_by_email(session, email)
    if tenant is None:
        raise ToolError(f"tenant not found for email: {email.strip().lower()}")
    return TenantResponse.model_validate(tenant)


@mcp.tool()
async def work_order_create(
    tenant_id: UUID,
    issue: str,
    unit: str | None = None,
    status: WorkOrderStatus = WorkOrderStatus.OPEN,
) -> WorkOrderResponse:
    """Create a maintenance work order for a tenant."""
    async with SessionLocal() as session:
        tenant = await tenants_repo.get_tenant_by_id(session, tenant_id)
        if tenant is None:
            raise ToolError(f"tenant not found for id: {tenant_id}")
        work_order = await work_orders_repo.create_work_order(
            session,
            WorkOrderCreate(
                tenant_id=tenant_id,
                unit=unit,
                issue=issue,
                status=status,
            ),
        )
    return WorkOrderResponse.model_validate(work_order)


@mcp.tool()
async def work_order_get(work_order_id: UUID) -> WorkOrderResponse:
    """Fetch a work order by id."""
    async with SessionLocal() as session:
        work_order = await work_orders_repo.get_work_order(session, work_order_id)
    if work_order is None:
        raise ToolError(f"work order not found for id: {work_order_id}")
    return WorkOrderResponse.model_validate(work_order)


@mcp.tool()
async def work_order_list(
    status: WorkOrderStatus | None = None,
) -> WorkOrderListResponse:
    """List work orders, optionally filtered by status."""
    async with SessionLocal() as session:
        items = await work_orders_repo.list_work_orders(session, status=status)
    return WorkOrderListResponse(
        items=[WorkOrderResponse.model_validate(item) for item in items]
    )


@mcp.tool()
async def work_order_update(
    work_order_id: UUID,
    unit: str | None = None,
    issue: str | None = None,
    status: WorkOrderStatus | None = None,
) -> WorkOrderResponse:
    """Update fields on an existing work order."""
    changes = {
        key: value
        for key, value in (("unit", unit), ("issue", issue), ("status", status))
        if value is not None
    }
    if not changes:
        raise ToolError("work_order_update requires at least one field to change")
    payload = WorkOrderUpdate.model_validate(changes)

    async with SessionLocal() as session:
        work_order = await work_orders_repo.get_work_order(session, work_order_id)
        if work_order is None:
            raise ToolError(f"work order not found for id: {work_order_id}")
        updated = await work_orders_repo.update_work_order(session, work_order, payload)
    return WorkOrderResponse.model_validate(updated)


@mcp.tool()
async def send_reply(email_id: UUID, draft_text: str) -> OutboxResponse:
    """Write a reply draft to the outbox (never sends real email)."""
    text = draft_text.strip()
    if not text:
        raise ToolError("draft_text must not be empty")

    async with SessionLocal() as session:
        email = await repo.get_email_by_id(session, email_id)
        if email is None:
            raise ToolError(f"email not found for id: {email_id}")
        entry = await outbox_repo.create_outbox_entry(
            session,
            OutboxCreate(email_id=email_id, draft_text=text),
        )
    return OutboxResponse.model_validate(entry)


@mcp.tool()
async def lease_qa(question: str, document_id: UUID) -> LeaseQAResponse:
    """Ask LeaseClear a lease question for a document."""
    text = question.strip()
    if not text:
        raise ToolError("question must not be empty")
    try:
        return await leaseclear.ask(text, document_id)
    except LeaseClearError as exc:
        raise ToolError(str(exc)) from exc
    except httpx.RequestError as exc:
        raise ToolError(f"LeaseClear unreachable: {exc}") from exc


if __name__ == "__main__":
    mcp.run()
