from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

from leaseops.core.config import settings

_LEASECLEAR_MCP = Path(__file__).resolve().parents[4].parent / "leaseclear-mcp"


class McpToolError(RuntimeError):
    """Raised when an MCP tool call fails or returns no structured content."""


def _error_text(result: CallToolResult) -> str:
    for block in result.content:
        if isinstance(block, TextContent):
            return block.text
    return str(result)


def _server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command="uvx",
        args=["--from", str(_LEASECLEAR_MCP), "leaseclear-mcp"],
        env={**os.environ, "LEASECLEAR_API_URL": settings.leaseclear_base_url},
    )


@asynccontextmanager
async def mcp_session() -> AsyncGenerator[ClientSession]:
    async with (
        stdio_client(_server_params()) as (read, write),  # pyright: ignore[reportGeneralTypeIssues]
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
