from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

from leaseops.core.config import settings

_BACKEND_ROOT = Path(__file__).resolve().parents[3]


class McpToolError(RuntimeError):
    """Raised when an MCP tool call fails or returns no structured content."""


def _error_text(result: CallToolResult) -> str:
    for block in result.content:
        if isinstance(block, TextContent):
            return block.text
    return str(result)


@asynccontextmanager
async def mcp_session() -> AsyncGenerator[ClientSession]:
    env = dict(os.environ)
    env["LEASECLEAR_BASE_URL"] = settings.leaseclear_base_url
    server = StdioServerParameters(
        command="uv",
        args=["run", "lease-qa-mcp"],
        cwd=str(_BACKEND_ROOT),
        env=env,
    )
    async with (
        stdio_client(server) as (read, write),  # pyright: ignore[reportGeneralTypeIssues]
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        yield session


async def call_tool(
    session: ClientSession,
    name: str,
    arguments: dict[str, object],
    *,
    meta: dict[str, object] | None = None,
) -> dict[str, object]:
    result = await session.call_tool(name, arguments=arguments, meta=meta)
    if result.isError:
        raise McpToolError(_error_text(result))
    if result.structuredContent is None:
        raise McpToolError(f"{name} returned no structuredContent")
    return result.structuredContent
