from __future__ import annotations

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from leaseops.clients import leaseclear
from leaseops.clients.leaseclear import LeaseClearError
from leaseops.db import tenants as tenants_repo
from leaseops.db.session import SessionLocal
from leaseops.models.schemas import LeaseQAResponse

mcp = FastMCP("leaseops", log_level="WARNING")


@mcp.tool()
async def lease_qa(
    question: str,
    tenant_name: str,
    address: str,
    unit: str | None = None,
) -> LeaseQAResponse:
    """Ask LeaseClear a lease question for a tenant identified by name/address/unit."""
    text = question.strip()
    if not text:
        raise ToolError("question must not be empty")
    async with SessionLocal() as session:
        tenant = await tenants_repo.get_tenant_by_identity(
            session, tenant_name, address, unit
        )
    if tenant is None:
        raise ToolError(
            "tenant not found for "
            f"name={tenant_name!r} address={address!r} unit={unit!r}"
        )
    try:
        return await leaseclear.ask(text, tenant.document_id)
    except LeaseClearError as exc:
        raise ToolError(str(exc)) from exc
    except httpx.RequestError as exc:
        raise ToolError(f"LeaseClear unreachable: {exc}") from exc


if __name__ == "__main__":
    mcp.run()
