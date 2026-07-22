from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from leaseops.db import tenants as tenants_repo
from leaseops.db.session import SessionLocal
from leaseops.models.schemas import TenantResponse

mcp = FastMCP("leaseops")


@mcp.tool()
async def tenant_lookup(email: str) -> TenantResponse:
    """Resolve a sender email to tenant, unit, and LeaseClear document id."""
    async with SessionLocal() as session:
        tenant = await tenants_repo.get_tenant_by_email(session, email)
    if tenant is None:
        raise ToolError(f"tenant not found for email: {email.strip().lower()}")
    return TenantResponse.model_validate(tenant)


if __name__ == "__main__":
    mcp.run()
