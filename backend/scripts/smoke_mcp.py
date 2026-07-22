from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import UUID

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent
from sqlalchemy import select

from leaseops.db.models import Email
from leaseops.db.session import SessionLocal
from leaseops.models.schemas import (
    LeaseQAResponse,
    OutboxResponse,
    TenantResponse,
    WorkOrderListResponse,
    WorkOrderResponse,
)

BACKEND_ROOT = Path(__file__).resolve().parent.parent
TENANT_EMAIL = "deshawn.johnson@example.com"


def _require_ok(result: CallToolResult, tool: str) -> dict[str, object]:
    if result.isError:
        text = ""
        for block in result.content:
            if isinstance(block, TextContent):
                text = block.text
                break
        raise RuntimeError(f"{tool} failed: {text or result}")
    if result.structuredContent is None:
        raise RuntimeError(f"{tool} returned no structuredContent")
    return result.structuredContent


async def _seed_email_id() -> UUID:
    async with SessionLocal() as session:
        email = (
            await session.scalars(
                select(Email).where(Email.sender == TENANT_EMAIL).limit(1)
            )
        ).first()
    if email is None:
        raise RuntimeError(
            f"no seeded email for {TENANT_EMAIL} — run: uv run python scripts/seed.py"
        )
    return email.id


async def _call(
    session: ClientSession, name: str, arguments: dict[str, object]
) -> dict[str, object]:
    print(f"→ {name}")
    result = await session.call_tool(name, arguments=arguments)
    payload = _require_ok(result, name)
    print(json.dumps(payload, indent=2, default=str))
    print()
    return payload


async def run(*, skip_lease_qa: bool) -> None:
    email_id = await _seed_email_id()

    server = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "leaseops.mcp.server"],
        cwd=str(BACKEND_ROOT),
        env=dict(os.environ),
    )

    async with (
        stdio_client(server) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        tools = await session.list_tools()
        names = sorted(t.name for t in tools.tools)
        print(f"tools: {names}\n")

        tenant = TenantResponse.model_validate(
            await _call(session, "tenant_lookup", {"email": TENANT_EMAIL})
        )

        created = WorkOrderResponse.model_validate(
            await _call(
                session,
                "work_order_create",
                {
                    "tenant_id": str(tenant.id),
                    "unit": tenant.unit or "unknown",
                    "issue": "MCP smoke test — kitchen sink drip",
                },
            )
        )

        WorkOrderResponse.model_validate(
            await _call(
                session,
                "work_order_get",
                {"work_order_id": str(created.id)},
            )
        )

        WorkOrderResponse.model_validate(
            await _call(
                session,
                "work_order_update",
                {
                    "work_order_id": str(created.id),
                    "status": "in_progress",
                },
            )
        )

        WorkOrderListResponse.model_validate(
            await _call(session, "work_order_list", {"status": "in_progress"})
        )

        OutboxResponse.model_validate(
            await _call(
                session,
                "send_reply",
                {
                    "email_id": str(email_id),
                    "draft_text": "Thanks — we'll send a plumber tomorrow.",
                },
            )
        )

        if skip_lease_qa:
            print("↷ lease_qa skipped (--skip-lease-qa)")
        else:
            LeaseQAResponse.model_validate(
                await _call(
                    session,
                    "lease_qa",
                    {
                        "question": "Who pays for gas?",
                        "document_id": str(tenant.document_id),
                    },
                )
            )

    print("ok — all MCP tools responded with structured results")


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test LeaseOps MCP tools")
    parser.add_argument(
        "--skip-lease-qa",
        action="store_true",
        help="Skip lease_qa (when LeaseClear is not running on LEASECLEAR_BASE_URL)",
    )
    args = parser.parse_args()
    try:
        asyncio.run(run(skip_lease_qa=args.skip_lease_qa))
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
