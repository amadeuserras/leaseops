from __future__ import annotations

from leaseops.agent.events import emit_tool_call, emit_tool_result
from leaseops.agent.state import AgentState
from leaseops.agent.types import PlanAction
from leaseops.mcp.client import call_tool, mcp_session


async def execute(state: AgentState) -> None:
    async with mcp_session() as session:
        for action in state.actions:
            if action == PlanAction.CREATE_WORK_ORDER:
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

            elif action == PlanAction.SEND_REPLY:
                reply_args: dict[str, object] = {
                    "email_id": str(state.email_id),
                    "draft_text": state.draft,
                }
                emit_tool_call("execute", "send_reply", reply_args)
                reply = await call_tool(session, "send_reply", reply_args)
                emit_tool_result("execute", "send_reply", reply)

            # call_tenant: no side-effect tool yet
