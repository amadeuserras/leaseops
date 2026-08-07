from __future__ import annotations

from typing import Any, cast

from langgraph.types import interrupt

from leaseops.agent.citations import first_citation
from leaseops.agent.enums import EmailCategory
from leaseops.agent.schemas import ApprovalCard, ApprovalOutput
from leaseops.agent.state import AgentState


def _approval_request(state: AgentState) -> ApprovalCard:
    if state.category == EmailCategory.EMERGENCY or state.responsibility is None:
        responsibility = None
    else:
        responsibility = state.responsibility.value

    return ApprovalCard(
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
        citation=first_citation(state.lease_check_steps),
        original_email=state.body,
        draft=state.draft,
        actions=[action.value for action in state.actions],
    )


def approval(state: AgentState) -> ApprovalOutput:
    raw = cast(
        dict[str, Any], interrupt(_approval_request(state).model_dump(mode="json"))
    )
    decision = ApprovalOutput.model_validate(raw)
    return ApprovalOutput(approved=decision.approved)
