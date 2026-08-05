from __future__ import annotations

from uuid import UUID

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from leaseops.clients import leaseclear
from leaseops.clients.leaseclear import LeaseClearError, LeaseQAResponse

mcp = FastMCP("leaseops", log_level="WARNING")


@mcp.tool()
async def lease_qa(question: str, document_id: UUID) -> LeaseQAResponse:
    """Ask LeaseClear a lease question scoped to one document."""
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
