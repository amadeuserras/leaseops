from __future__ import annotations

from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic import BaseModel

from leaseops.agent.events import emit_cost
from leaseops.agent.state import AgentState, Severity
from leaseops.core.config import settings
from leaseops.db import tenants as tenants_repo
from leaseops.db.models import Tenant
from leaseops.db.session import SessionLocal

_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = """\
You extract structured fields from a residential property-manager email.

Fill these fields from the subject and body only:

- severity: high | medium | low
- appliance_or_system: the specific appliance or system named (e.g. "dishwasher",
  "furnace", "front door lock"); otherwise null
- issue_summary: a neutral factual restatement of the reported problem,
  including, if stated: what is affected, duration, suspected cause, and any
  circumstances bearing on responsibility (damage, misuse, prior repairs,
  previous reports of the same issue). Do not include the tenant's wording,
  emotions, or accusations.

Rules:
- Do not invent details that are not in the email.
"""


class _ExtractFormat(BaseModel):
    severity: Severity
    appliance_or_system: str | None = None
    issue_summary: str


@dataclass(frozen=True)
class _ExtractResult:
    tenant_name: str | None
    unit: str | None
    address: str | None
    issue_summary: str
    severity: Severity
    appliance_or_system: str | None


def _content_message(state: AgentState) -> str:
    return f"Subject: {state.subject}\n\nBody:\n{state.body}"


async def _extract_fields(state: AgentState) -> _ExtractFormat:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    completion = await client.chat.completions.parse(
        model=_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _content_message(state)},
        ],
        response_format=_ExtractFormat,
    )
    if completion.usage is not None:
        emit_cost(
            "extract",
            _MODEL,
            completion.usage.prompt_tokens,
            completion.usage.completion_tokens,
        )
    result = completion.choices[0].message.parsed
    if result is None:
        raise RuntimeError("extract: model returned no parsed output")
    return result


async def _lookup_tenant(sender: str) -> Tenant | None:
    async with SessionLocal() as session:
        return await tenants_repo.get_tenant_by_email(session, sender)


async def extract(state: AgentState) -> _ExtractResult:
    fields = await _extract_fields(state)
    tenant = await _lookup_tenant(state.sender)
    return _ExtractResult(
        tenant_name=tenant.name if tenant else None,
        unit=tenant.unit if tenant else None,
        address=tenant.address if tenant else None,
        issue_summary=fields.issue_summary,
        severity=fields.severity,
        appliance_or_system=fields.appliance_or_system,
    )
