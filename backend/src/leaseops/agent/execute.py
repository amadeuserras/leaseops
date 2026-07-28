from __future__ import annotations

from dataclasses import dataclass

from leaseops.agent.state import ActionType, AgentState, Status
from leaseops.mcp.client import call_tool, mcp_session


@dataclass(frozen=True)
class _ExecuteResult:
    status: Status


async def execute(state: AgentState) -> _ExecuteResult:
    action = state.action_type

    async with mcp_session() as session:
        if action == ActionType.CREATE_WORK_ORDER:
            tenant = await call_tool(session, "tenant_lookup", {"email": state.sender})

            await call_tool(
                session,
                "work_order_create",
                {
                    "tenant_id": str(tenant["id"]),
                    "issue": state.issue_summary,
                },
            )
        elif action == ActionType.SEND_REPLY:
            await call_tool(
                session,
                "send_reply",
                {
                    "email_id": str(state.email_id),
                    "draft_text": state.draft,
                },
            )

    return _ExecuteResult(status=Status.DONE)
