# ruff: noqa: E501

from __future__ import annotations

from anthropic import AsyncAnthropic, transform_schema
from anthropic.types import (
    Message,
    MessageParam,
    TextBlock,
    ToolChoiceParam,
    ToolParam,
    ToolResultBlockParam,
    ToolUseBlock,
)
from pydantic import BaseModel, Field, ValidationError

from leaseops.agent.citations import extract_citation_ids
from leaseops.agent.enums import Responsibility
from leaseops.agent.events import emit_cost, emit_tool_call, emit_tool_result
from leaseops.agent.schemas import (
    LeaseCheckOutput,
    LeaseCheckStep,
    LeaseQaTool,
    SubmitVerdictTool,
)
from leaseops.agent.state import AgentState
from leaseops.clients.leaseclear import LeaseQAResponse
from leaseops.core.config import settings
from leaseops.mcp.client import McpToolError, call_tool, mcp_session

_ACTOR_MODEL = "claude-sonnet-4-6"
_MAX_QA_CALLS = 4
_MAX_TOKENS = 2048

_SYSTEM_PROMPT = """\
Decide who is responsible for the tenant's request using only the lease answers provided.

Ask questions about the reported issue, then call submit_verdict when you're ready to draw a conclusion. Reason and infer the verdict from the lease_qa answers, not outside knowledge. Always include 1–2 short reasoning sentences with each tool call, and ensure the submitted responsibility matches that reasoning. 

lease_qa calls remaining: {remaining} / {max_calls}
"""


class _LeaseQaFormat(BaseModel):
    question: str = Field(
        description="A single neutral question about lease terms.",
    )


class _SubmitVerdictFormat(BaseModel):
    reasoning: str = Field(
        description=(
            "Brief explanation of how the lease evidence leads to this verdict."
        ),
    )
    lease_addresses_issue: bool = Field(
        description="True if the lease speaks to this issue at all.",
    )
    responsibility: Responsibility = Field(
        description="Who the lease assigns responsibility to.",
    )


LEASE_QA_TOOL: ToolParam = {
    "name": "lease_qa",
    "description": (
        "Ask one neutral, precise question about the tenant's lease. "
        "The lease document is already scoped for this email. Returns an "
        "answer grounded in the lease, or states that the lease does not "
        "address the question."
    ),
    "strict": True,
    "input_schema": transform_schema(_LeaseQaFormat.model_json_schema()),
}

SUBMIT_VERDICT_TOOL: ToolParam = {
    "name": "submit_verdict",
    "description": (
        "Submit the final responsibility verdict for the email's main request."
    ),
    "strict": True,
    "input_schema": transform_schema(_SubmitVerdictFormat.model_json_schema()),
}


def _task_message(state: AgentState) -> str:
    tenant = state.tenant_name or "not specified"
    unit = state.unit or "not specified"
    address = state.address or "not specified"
    system = state.appliance_or_system or "not specified"
    severity = state.severity.value if state.severity else "not specified"
    summary = state.issue_summary or "not specified"
    return (
        "Tenant:\n"
        f"- Name: {tenant}\n"
        f"- Address: {address}\n"
        f"- Unit: {unit}\n\n"
        "Reported issue:\n"
        f"- System/appliance involved: {system}\n"
        f"- Severity: {severity}\n"
        f"- Summary: {summary}\n\n"
    )


def _find_tool_use(response: Message, name: str) -> ToolUseBlock | None:
    for block in response.content:
        if isinstance(block, ToolUseBlock) and block.name == name:
            return block
    return None


def _response_text(response: Message) -> str:
    parts = [block.text for block in response.content if isinstance(block, TextBlock)]
    return "\n".join(parts).strip()


def _qa_call_count(steps: list[LeaseCheckStep]) -> int:
    return sum(1 for step in steps if step.tool.name == "lease_qa")


def _verdict_output(
    *,
    responsibility: Responsibility,
    lease_addresses_issue: bool,
    steps: list[LeaseCheckStep],
    reasoning: str,
) -> LeaseCheckOutput:
    steps.append(
        LeaseCheckStep(
            reasoning=reasoning,
            tool=SubmitVerdictTool(
                lease_addresses_issue=lease_addresses_issue,
                responsibility=responsibility,
            ),
        )
    )
    return LeaseCheckOutput(
        responsibility=responsibility,
        lease_addresses_issue=lease_addresses_issue,
        lease_check_steps=steps,
    )


async def lease_check(state: AgentState) -> LeaseCheckOutput:
    if state.document_id is None:
        return _verdict_output(
            responsibility=Responsibility.UNCLEAR,
            lease_addresses_issue=False,
            steps=[],
            reasoning="",
        )

    messages: list[MessageParam] = [{"role": "user", "content": _task_message(state)}]
    steps: list[LeaseCheckStep] = []

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    async with mcp_session() as session:
        while True:
            used = _qa_call_count(steps)
            remaining = max(_MAX_QA_CALLS - used, 0)
            force_verdict = remaining == 0
            tool_choice: ToolChoiceParam = (
                {
                    "type": "tool",
                    "name": "submit_verdict",
                    "disable_parallel_tool_use": True,
                }
                if force_verdict
                else {"type": "auto", "disable_parallel_tool_use": True}
            )

            response = await client.messages.create(
                model=_ACTOR_MODEL,
                max_tokens=_MAX_TOKENS,
                system=_SYSTEM_PROMPT.format(
                    remaining=remaining,
                    max_calls=_MAX_QA_CALLS,
                ),
                messages=messages,
                tools=[LEASE_QA_TOOL, SUBMIT_VERDICT_TOOL],
                tool_choice=tool_choice,
            )
            emit_cost(
                "lease_check",
                _ACTOR_MODEL,
                response.usage.input_tokens,
                response.usage.output_tokens,
            )
            messages.append({"role": "assistant", "content": response.content})

            verdict_use = _find_tool_use(response, "submit_verdict")
            if verdict_use is not None:
                try:
                    verdict = _SubmitVerdictFormat.model_validate(verdict_use.input)
                except ValidationError:
                    return _verdict_output(
                        responsibility=Responsibility.UNCLEAR,
                        lease_addresses_issue=False,
                        steps=steps,
                        reasoning=_response_text(response),
                    )
                # Prefer tool-arg reasoning: forced tool_choice often skips text.
                reasoning = verdict.reasoning.strip() or _response_text(response)
                return _verdict_output(
                    responsibility=verdict.responsibility,
                    lease_addresses_issue=verdict.lease_addresses_issue,
                    steps=steps,
                    reasoning=reasoning,
                )

            qa_use = _find_tool_use(response, "lease_qa")
            if qa_use is None:
                return _verdict_output(
                    responsibility=Responsibility.UNCLEAR,
                    lease_addresses_issue=False,
                    steps=steps,
                    reasoning=_response_text(response),
                )

            qa = _LeaseQaFormat.model_validate(qa_use.input)
            question = qa.question
            reasoning = _response_text(response)
            tool_args: dict[str, object] = {
                "question": question,
                "document_id": str(state.document_id),
            }
            emit_tool_call("lease_check", "lease_qa", tool_args, reasoning=reasoning)
            try:
                qa_result = await call_tool(session, "lease_qa", tool_args)
                answer = LeaseQAResponse.model_validate(qa_result).answer
                is_error = False
            except McpToolError as exc:
                answer = str(exc)
                is_error = True
            emit_tool_result("lease_check", "lease_qa", answer, is_error=is_error)

            steps.append(
                LeaseCheckStep(
                    reasoning=reasoning,
                    tool=LeaseQaTool(
                        question=question,
                        answer=answer,
                        citations=extract_citation_ids(answer),
                    ),
                )
            )
            tool_result: ToolResultBlockParam = {
                "type": "tool_result",
                "tool_use_id": qa_use.id,
                "content": answer,
            }
            if is_error:
                tool_result["is_error"] = True
            messages.append({"role": "user", "content": [tool_result]})
