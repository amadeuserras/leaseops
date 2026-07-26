from __future__ import annotations

from dataclasses import dataclass

from leaseops.agent.state import ActionType, AgentState, Status
from leaseops.policy.decide import decide as policy_decide


@dataclass(frozen=True)
class _DecideResult:
    action_type: ActionType
    summary: str
    status: Status


def decide(state: AgentState) -> _DecideResult:
    decision = policy_decide(state)
    status = (
        Status.ESCALATED
        if decision.action_type == ActionType.ESCALATE
        else Status.IN_PROGRESS
    )
    return _DecideResult(
        action_type=decision.action_type,
        summary=decision.summary,
        status=status,
    )
