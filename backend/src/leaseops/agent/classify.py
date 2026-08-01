from __future__ import annotations

from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic import BaseModel

from leaseops.agent.events import emit_cost
from leaseops.agent.state import AgentState, EmailCategory
from leaseops.core.config import settings

_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = """\
You classify inbound emails for a residential property manager.

Pick exactly one category:

- maintenance: repair/fix requests (leaks, HVAC, appliances, pests,
  access issues, etc.)
- lease_question: asks what the lease allows/requires (paint, pets,
  parking, guests, etc.)
- not_our_problem: spam, sales, wrong address, unrelated personal mail,
  or clearly not PM business
- emergency: immediate safety risk — gas smell, active flooding, fire,
  sparking electrical, carbon monoxide, structural collapse risk, or
  similar. When in doubt between maintenance and emergency, choose
  emergency.

Classify from the subject and body only. Do not invent details.
"""


class _ClassifyFormat(BaseModel):
    category: EmailCategory


@dataclass(frozen=True)
class _ClassifyResult:
    category: EmailCategory


def _content_message(state: AgentState) -> str:
    return f"Subject: {state.subject}\n\nBody:\n{state.body}"


async def classify(state: AgentState) -> _ClassifyResult:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    completion = await client.chat.completions.parse(
        model=_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _content_message(state)},
        ],
        response_format=_ClassifyFormat,
    )
    if completion.usage is not None:
        emit_cost(
            "classify",
            _MODEL,
            completion.usage.prompt_tokens,
            completion.usage.completion_tokens,
        )
    result = completion.choices[0].message.parsed
    if result is None:
        raise RuntimeError("classify: model returned no parsed output")
    return _ClassifyResult(category=result.category)
