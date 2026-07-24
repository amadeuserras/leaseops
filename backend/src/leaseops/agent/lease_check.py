from __future__ import annotations

import json
from typing import cast

from anthropic import AsyncAnthropic, transform_schema
from anthropic.types import (
    Message,
    MessageParam,
    ToolChoiceParam,
    ToolParam,
    ToolResultBlockParam,
    ToolUseBlock,
)
from pydantic import BaseModel, Field

from leaseops.agent.state import AgentState, QAResultSchema, Responsibility
from leaseops.core.config import settings
from leaseops.mcp.client import McpToolError, call_tool, mcp_session
from leaseops.models.schemas import LeaseQAResponse

_ACTOR_MODEL = "claude-sonnet-4-5"
_MAX_QA_CALLS = 3
_MAX_TOKENS = 1024

_LEASE_CHECK_SYSTEM = """\
You are the lease-analysis step inside a maintenance triage system for \
residential rental properties. A tenant has reported an issue. Your job is to \
determine what the lease says about it, using the lease_qa tool, and then \
submit a structured verdict.

## Your tools
- lease_qa: asks a question about the tenant's lease. Returns an answer, or \
states that the lease does not address the question. This tool queries only \
the relevant tenant's lease — you do not choose the document.
- submit_verdict: ends your work by recording your determination. You must \
always finish by calling this, and only once.

## How to ask good questions
- Ask about lease terms in neutral, precise language: \
"Who is responsible for repair and maintenance of the heating system?" — \
not "the tenant says the heating is broken again, whose fault is it?"
- Never include the tenant's own wording, emotions, or accusations in a \
question. You are querying a legal document, not relaying a complaint.
- One question per call. Start with the most direct responsibility question \
for the reported issue.
- Ask a follow-up ONLY if the first answer makes it necessary: it cross-\
references another section, it distinguishes cases you cannot resolve (e.g. \
negligence vs. normal wear) and the distinction matters, or it partially \
answers. You have a maximum of {max_calls} lease_qa calls; most cases need \
exactly one.

## How to reach a verdict
- Base your verdict ONLY on the answers returned by lease_qa. Do not use \
general knowledge of landlord-tenant law.
- If lease_qa states the lease does not address the issue, set \
lease_addresses_issue to false. This is a normal, correct outcome — do not \
stretch a tangentially related clause to force an answer.
- Distinguish carefully:
  - lease is SILENT → lease_addresses_issue: false, responsibility: unclear
  - lease SPEAKS but responsibility genuinely depends on facts you don't \
have → lease_addresses_issue: true, responsibility: unclear
"""


class _Verdict(BaseModel):
    lease_addresses_issue: bool = Field(
        description="True if the lease speaks to this issue at all."
    )
    responsibility: Responsibility = Field(
        description="Who the lease assigns responsibility to."
    )


class _LeaseCheckResult(_Verdict):
    qa_results: list[QAResultSchema] = []


LEASE_QA_TOOL: ToolParam = {
    "name": "lease_qa",
    "description": (
        "Ask one neutral, precise question about the tenant's lease. "
        "Returns an answer grounded in the lease, or states that the lease "
        "does not address the question."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "A single neutral question about lease terms.",
            }
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

SUBMIT_VERDICT_TOOL: ToolParam = {
    "name": "submit_verdict",
    "description": "Record the final determination and end the analysis.",
    "strict": True,
    "input_schema": transform_schema(_Verdict.model_json_schema()),
}


def _task_message(state: AgentState) -> str:
    category = state.issue_category.value if state.issue_category else "not specified"
    urgency = state.urgency.value if state.urgency else "not specified"
    system = state.appliance_or_system or "not specified"
    summary = state.issue_summary or "not specified"
    return (
        "Reported issue:\n"
        f"- Category: {category}\n"
        f"- System/appliance involved: {system}\n"
        f"- Urgency: {urgency}\n"
        f"- Summary: {summary}\n\n"
    )


def _find_tool_use(response: Message, name: str) -> ToolUseBlock | None:
    for block in response.content:
        if isinstance(block, ToolUseBlock) and block.name == name:
            return block
    return None


async def lease_check(state: AgentState) -> _LeaseCheckResult:
    if state.document_id is None:
        return _LeaseCheckResult(
            responsibility=Responsibility.UNCLEAR,
            lease_addresses_issue=False,
        )

    system_prompt = _LEASE_CHECK_SYSTEM.format(max_calls=_MAX_QA_CALLS)
    messages: list[MessageParam] = [{"role": "user", "content": _task_message(state)}]
    qa_results: list[QAResultSchema] = []

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    async with mcp_session() as session:
        while True:
            force_verdict = len(qa_results) >= _MAX_QA_CALLS
            tool_choice: ToolChoiceParam = (
                {"type": "tool", "name": "submit_verdict"}
                if force_verdict
                else {"type": "auto"}
            )

            response = await client.messages.create(
                model=_ACTOR_MODEL,
                max_tokens=_MAX_TOKENS,
                system=system_prompt,
                messages=messages,
                tools=[LEASE_QA_TOOL, SUBMIT_VERDICT_TOOL],
                tool_choice=tool_choice,
            )
            messages.append({"role": "assistant", "content": response.content})
            print(json.dumps(messages, indent=2, default=str))

            verdict_use = _find_tool_use(response, "submit_verdict")
            if verdict_use is not None:
                return _LeaseCheckResult(
                    responsibility=Responsibility(verdict_use.input["responsibility"]),
                    lease_addresses_issue=bool(
                        verdict_use.input["lease_addresses_issue"]
                    ),
                    qa_results=qa_results,
                )

            qa_use = _find_tool_use(response, "lease_qa")
            if qa_use is None:
                return _LeaseCheckResult(
                    responsibility=Responsibility.UNCLEAR,
                    lease_addresses_issue=False,
                    qa_results=qa_results,
                )

            question = cast(str, qa_use.input["question"])
            try:
                qa_result = await call_tool(
                    session,
                    "lease_qa",
                    {"question": question, "document_id": str(state.document_id)},
                )
                answer = LeaseQAResponse.model_validate(qa_result).answer
                is_error = False
            except McpToolError as exc:
                answer = str(exc)
                is_error = True

            qa_results.append(QAResultSchema(question=question, answer=answer))
            tool_result: ToolResultBlockParam = {
                "type": "tool_result",
                "tool_use_id": qa_use.id,
                "content": answer,
            }
            if is_error:
                tool_result["is_error"] = True
            messages.append({"role": "user", "content": [tool_result]})
