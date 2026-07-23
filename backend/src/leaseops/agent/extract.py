from __future__ import annotations

from openai import AsyncOpenAI
from pydantic import BaseModel

from leaseops.agent.state import AgentState, IssueCategory, Urgency
from leaseops.core.config import settings

_SYSTEM_PROMPT = """\
You extract structured fields from a residential property-manager email.

Fill these fields from the subject and body only:

- tenant_name: the tenant's name if stated; otherwise null
- unit: unit / apartment number if stated; otherwise null
- address: street address / building if stated; otherwise null
- issue_category: plumbing | electrical | hvac | appliance | structural |
  pest | access | other
- urgency: low | medium | high | emergency
- appliance_or_system: the specific appliance or system named (e.g. "dishwasher",
  "furnace", "front door lock"); otherwise null

Rules:
- Do not invent details that are not in the email.
- If the unit, address, or tenant name is missing or ambiguous, use null.
- Prefer emergency urgency only for immediate safety risks (gas, active flooding,
  fire, sparking electrical, CO, collapse risk).
"""


class _Extraction(BaseModel):
    tenant_name: str | None = None
    unit: str | None = None
    address: str | None = None
    issue_category: IssueCategory
    urgency: Urgency
    appliance_or_system: str | None = None


def _content_message(state: AgentState) -> str:
    return f"Subject: {state.subject}\n\nBody:\n{state.body}"


async def extract(state: AgentState) -> dict[str, str | IssueCategory | Urgency | None]:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    completion = await client.chat.completions.parse(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _content_message(state)},
        ],
        response_format=_Extraction,
    )
    result = completion.choices[0].message.parsed
    if result is None:
        raise RuntimeError("extract: model returned no parsed output")
    return {
        "tenant_name": result.tenant_name,
        "unit": result.unit,
        "address": result.address,
        "issue_category": result.issue_category,
        "urgency": result.urgency,
        "appliance_or_system": result.appliance_or_system,
    }
