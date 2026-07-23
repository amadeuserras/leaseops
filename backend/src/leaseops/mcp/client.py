from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

_BACKEND_ROOT = Path(__file__).resolve().parents[3]


class McpToolError(RuntimeError):
    """Raised when an MCP tool call fails or returns no structured content."""


def _error_text(result: CallToolResult) -> str:
    for block in result.content:
        if isinstance(block, TextContent):
            return block.text
    return str(result)


def require_ok(result: CallToolResult, tool: str) -> dict[str, object]:
    if result.isError:
        raise McpToolError(f"{tool} failed: {_error_text(result)}")
    if result.structuredContent is None:
        raise McpToolError(f"{tool} returned no structuredContent")
    return result.structuredContent


@asynccontextmanager
async def mcp_session() -> AsyncGenerator[ClientSession]:
    server = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "leaseops.mcp.server"],
        cwd=str(_BACKEND_ROOT),
        env=dict(os.environ),
    )
    async with (
        stdio_client(server) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        yield session


async def call_tool(
    session: ClientSession,
    name: str,
    arguments: dict[str, object],
) -> dict[str, object]:
    result = await session.call_tool(name, arguments=arguments)
    return require_ok(result, name)
