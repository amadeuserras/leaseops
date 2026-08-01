from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, cast
from uuid import UUID

from langgraph.types import interrupt

from leaseops.agent.state import AgentState


@dataclass(frozen=True)
class ApprovalRequest:
    email_id: UUID
    actions: list[str]
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


def _approval_request(state: AgentState) -> ApprovalRequest:
    return ApprovalRequest(
        email_id=state.email_id,
        actions=[action.value for action in state.actions],
        draft=state.draft,
        tenant_name=state.tenant_name,
        unit=state.unit,
        issue_summary=state.issue_summary,
    )


def approval(state: AgentState) -> _ApprovalResult:
    raw = cast(dict[str, Any], interrupt(asdict(_approval_request(state))))
    decision = ApprovalDecision(**raw)
    if decision.approved:
        return _ApprovalResult(approved=True, rejection_reason=None)
    return _ApprovalResult(
        approved=False,
        rejection_reason=decision.rejection_reason,
    )
