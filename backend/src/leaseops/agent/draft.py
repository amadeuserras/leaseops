from __future__ import annotations

from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic import BaseModel

from leaseops.agent.events import emit_cost
from leaseops.agent.state import AgentState
from leaseops.agent.types import QAResultSchema
from leaseops.core.config import settings

_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = """\
You draft a reply email from a residential property manager to a tenant.

Write the reply body only — no subject line, no markdown, no preamble about
what you are doing.

## Grounding
- Base lease claims ONLY on the provided lease Q&A answers. Those answers
  already include citations inline (clause/section references). When you
  rely on a lease point, keep that citation text in the reply so the tenant
  can see where it came from.
- Do not invent lease terms, clause numbers, or policies that are not in
  the Q&A answers.
- If the lease does not address the issue, or Q&A is empty, do not pretend
  otherwise — draft from the decision summary and known facts only.

## Tone and content
- Professional, calm, concise. Acknowledge the reported issue briefly.
- Match the decided action:
  - create_work_order: confirm landlord responsibility (citing the lease
    when available) and that a work order will be opened / a technician
    scheduled.
  - send_reply: answer the question or explain tenant responsibility,
    citing the lease when available. Do not promise a work order.
  - no_action: brief holding reply — someone will follow up; do not invent
    next steps or lease conclusions.
- Do not mention internal systems, agents, confidence, or escalation
  machinery.
"""


class _DraftFormat(BaseModel):
    draft: str


@dataclass(frozen=True)
class _DraftResult:
    draft: str


def _format_qa_results(qa_results: list[QAResultSchema]) -> str:
    if not qa_results:
        return "(none)"
    parts: list[str] = []
    for i, qa in enumerate(qa_results, start=1):
        parts.append(f"{i}. Q: {qa.question}\n   A: {qa.answer}")
    return "\n".join(parts)


def _content_message(state: AgentState) -> str:
    action = state.action_type.value if state.action_type else "unknown"
    responsibility = state.responsibility.value if state.responsibility else "unknown"
    summary = state.summary or "(none)"
    issue = state.issue_summary or "(none)"
    tenant = state.tenant_name or "(not stated)"
    unit = state.unit or "(not stated)"
    return (
        f"Tenant: {tenant}\n"
        f"Unit: {unit}\n"
        f"Original subject: {state.subject}\n"
        f"Original body:\n{state.body}\n\n"
        f"Issue summary: {issue}\n"
        f"Lease addresses issue: {state.lease_addresses_issue}\n"
        f"Responsibility: {responsibility}\n"
        f"Decided action: {action}\n"
        f"Decision summary: {summary}\n\n"
        f"Lease Q&A (citations are inline in the answers):\n"
        f"{_format_qa_results(state.qa_results)}\n"
    )


async def draft(state: AgentState) -> _DraftResult:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    completion = await client.chat.completions.parse(
        model=_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _content_message(state)},
        ],
        response_format=_DraftFormat,
    )
    if completion.usage is not None:
        emit_cost(
            "draft",
            _MODEL,
            completion.usage.prompt_tokens,
            completion.usage.completion_tokens,
        )
    result = completion.choices[0].message.parsed
    if result is None:
        raise RuntimeError("draft: model returned no parsed output")
    return _DraftResult(draft=result.draft.strip())
