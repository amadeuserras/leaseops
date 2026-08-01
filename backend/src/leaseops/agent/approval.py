from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, cast
from uuid import UUID

from langgraph.types import interrupt

from leaseops.agent.citations import first_citation
from leaseops.agent.state import AgentState, EmailCategory


@dataclass(frozen=True)
class ApprovalRequest:
    email_id: UUID
    category: str
    severity: str | None
    received_at: str
    tenant_name: str | None
    unit: str | None
    address: str | None
    issue_summary: str | None
    appliance_or_system: str | None
    responsibility: str | None
    citation: str | None
    original_email: str
    draft: str | None
    actions: list[str]


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool


@dataclass(frozen=True)
class _ApprovalResult:
    approved: bool


def _approval_request(state: AgentState) -> ApprovalRequest:
    if state.category == EmailCategory.EMERGENCY or state.responsibility is None:
        responsibility = None
    else:
        responsibility = state.responsibility.value

    return ApprovalRequest(
        email_id=state.email_id,
        category=state.category.value if state.category else "maintenance",
        severity=state.severity.value if state.severity else None,
        received_at=state.received_at.isoformat(),
        tenant_name=state.tenant_name,
        unit=state.unit,
        address=state.address,
        issue_summary=state.issue_summary,
        appliance_or_system=state.appliance_or_system,
        responsibility=responsibility,
        citation=first_citation(state.qa_results),
        original_email=state.body,
        draft=state.draft,
        actions=[action.value for action in state.actions],
    )


def approval(state: AgentState) -> _ApprovalResult:
    raw = cast(dict[str, Any], interrupt(asdict(_approval_request(state))))
    decision = ApprovalDecision(**raw)
    return _ApprovalResult(approved=decision.approved)
