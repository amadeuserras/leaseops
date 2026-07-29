from __future__ import annotations

from dataclasses import dataclass

from leaseops.agent.events import emit_tool_call, emit_tool_result
from leaseops.agent.state import AgentState
from leaseops.agent.types import ActionType, Status
from leaseops.mcp.client import call_tool, mcp_session


@dataclass(frozen=True)
class _ExecuteResult:
    status: Status


async def execute(state: AgentState) -> _ExecuteResult:
    action = state.action_type

    async with mcp_session() as session:
        if action == ActionType.CREATE_WORK_ORDER:
            lookup_args: dict[str, object] = {"email": state.sender}
            emit_tool_call("execute", "tenant_lookup", lookup_args)
            tenant = await call_tool(session, "tenant_lookup", lookup_args)
            emit_tool_result("execute", "tenant_lookup", tenant)

            order_args: dict[str, object] = {
                "email_id": str(state.email_id),
                "tenant_id": str(tenant["id"]),
                "issue": state.issue_summary,
            }
            emit_tool_call("execute", "work_order_create", order_args)
            order = await call_tool(session, "work_order_create", order_args)
            emit_tool_result("execute", "work_order_create", order)

        elif action == ActionType.SEND_REPLY:
            reply_args: dict[str, object] = {
                "email_id": str(state.email_id),
                "draft_text": state.draft,
            }
            emit_tool_call("execute", "send_reply", reply_args)
            reply = await call_tool(session, "send_reply", reply_args)
            emit_tool_result("execute", "send_reply", reply)

    return _ExecuteResult(status=Status.DONE)
