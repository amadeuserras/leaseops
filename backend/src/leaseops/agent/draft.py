from __future__ import annotations

from openai import AsyncOpenAI
from pydantic import BaseModel

from leaseops.agent.events import emit_cost
from leaseops.agent.schemas import DraftOutput, LeaseCheckStep, LeaseQaTool
from leaseops.agent.state import AgentState
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
  otherwise — draft from the known facts only.

## Tone and content
- Short and personable — like a capable property manager. Warm but measured; 
not bubbly or chatty. Aim for ~2–4 sentences.
- Address them by first name when known. Lead with a brief, calm
  acknowledgment ("thanks for asking", "sorry about the hassle"), then
  the answer with the lease citation, then one clear next step or offer.
- If responsibility is landlord: confirm you'll arrange repair / open a
  work order, citing the lease when available.
- If responsibility is tenant: explain what's needed, citing the lease
  when available. Offer to help where it makes sense (e.g. submit a
  consent request). Do not promise a work order.
- If responsibility is shared, unclear, or missing: acknowledge the
  report and say someone will follow up; do not invent next steps or
  lease conclusions.
- For emergencies: prioritize safety instructions; do not invent lease
  analysis.

## Example vibe
"Hi Priya, thanks for asking — the lease requires the landlord's prior
written consent before painting (lease-agreement-final-v3-1 §6(1)), so
you'd need approval before proceeding. Let me know if you'd like me to 
submit that request on your behalf."
"""


class _DraftFormat(BaseModel):
    draft: str


def _format_lease_check_steps(steps: list[LeaseCheckStep]) -> str:
    qa_steps = [s for s in steps if isinstance(s.tool, LeaseQaTool)]
    if not qa_steps:
        return "(none)"
    parts: list[str] = []
    for i, step in enumerate(qa_steps, start=1):
        tool = step.tool
        assert isinstance(tool, LeaseQaTool)
        parts.append(f"{i}. Q: {tool.question}\n   A: {tool.answer}")
    return "\n".join(parts)


def _content_message(state: AgentState) -> str:
    category = state.category.value if state.category else "unknown"
    responsibility = state.responsibility.value if state.responsibility else "unknown"
    issue = state.issue_summary or "(none)"
    tenant = state.tenant_name or "(not stated)"
    unit = state.unit or "(not stated)"
    return (
        f"Tenant: {tenant}\n"
        f"Unit: {unit}\n"
        f"Category: {category}\n"
        f"Original subject: {state.subject}\n"
        f"Original body:\n{state.body}\n\n"
        f"Issue summary: {issue}\n"
        f"Lease addresses issue: {state.lease_addresses_issue}\n"
        f"Responsibility: {responsibility}\n\n"
        f"Lease Q&A (citations are inline in the answers):\n"
        f"{_format_lease_check_steps(state.lease_check_steps)}\n"
    )


async def draft(state: AgentState) -> DraftOutput:
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
    return DraftOutput(draft=result.draft.strip())
