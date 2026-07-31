from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, cast
from uuid import UUID

from langgraph.types import interrupt

from leaseops.agent.state import AgentState
from leaseops.agent.types import Status


@dataclass(frozen=True)
class ApprovalRequest:
    email_id: UUID
    action_type: str
    summary: str | None
    draft: str | None
    tenant_name: str | None
    unit: str | None
    issue_summary: str | None


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    rejection_reason: str | None = None


@dataclass(frozen=True)
class _ApprovalResult:
    approved: bool
    rejection_reason: str | None
    status: Status


def _approval_request(state: AgentState) -> ApprovalRequest:
    action = state.action_type
    assert action is not None
    return ApprovalRequest(
        email_id=state.email_id,
        action_type=action.value,
        summary=state.summary,
        draft=state.draft,
        tenant_name=state.tenant_name,
        unit=state.unit,
        issue_summary=state.issue_summary,
    )


def approval_gate(state: AgentState) -> _ApprovalResult:
    raw = cast(dict[str, Any], interrupt(asdict(_approval_request(state))))
    decision = ApprovalDecision(**raw)
    if decision.approved:
        return _ApprovalResult(
            approved=True,
            rejection_reason=None,
            status=Status.IN_PROGRESS,
        )
    return _ApprovalResult(
        approved=False,
        rejection_reason=decision.rejection_reason,
        status=Status.REJECTED,
    )
