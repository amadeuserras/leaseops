from __future__ import annotations

from dataclasses import dataclass

from leaseops.agent.state import (
    ActionType,
    AgentState,
    EmailCategory,
    Responsibility,
    Urgency,
)
from leaseops.policy.whitelist import clamp_action


@dataclass(frozen=True)
class _Decision:
    action_type: ActionType
    summary: str


def _decide(state: AgentState) -> _Decision:
    if state.category == EmailCategory.EMERGENCY or state.urgency == Urgency.EMERGENCY:
        return _Decision(
            ActionType.ESCALATE,
            "Emergency safety risk — escalate to a human immediately.",
        )

    if state.category == EmailCategory.NOT_OUR_PROBLEM:
        return _Decision(
            ActionType.NO_ACTION,
            "Email is outside property-management scope.",
        )

    if state.category == EmailCategory.LEASE_QUESTION:
        lease_clear = (
            state.lease_addresses_issue is True
            and state.responsibility != Responsibility.UNCLEAR
        )
        if lease_clear:
            return _Decision(
                ActionType.SEND_REPLY,
                "Lease addresses the question; draft a cited reply.",
            )
        return _Decision(
            ActionType.ESCALATE,
            "Lease is silent or unclear on the question.",
        )

    # maintenance (and any unexpected category): require identity + a clear lease call
    if state.document_id is None:
        return _Decision(
            ActionType.ESCALATE,
            "Tenant identity is missing or unresolved.",
        )

    if state.lease_addresses_issue is not True:
        return _Decision(
            ActionType.ESCALATE,
            "Lease does not address the reported issue.",
        )

    if state.responsibility == Responsibility.LANDLORD:
        return _Decision(
            ActionType.CREATE_WORK_ORDER,
            "Lease assigns repair responsibility to the landlord.",
        )

    if state.responsibility == Responsibility.TENANT:
        return _Decision(
            ActionType.SEND_REPLY,
            "Lease assigns responsibility to the tenant; explain and close.",
        )

    return _Decision(
        ActionType.ESCALATE,
        "Responsibility is shared or unclear — needs human judgment.",
    )


def decide(state: AgentState) -> _Decision:
    decision = _decide(state)
    return _Decision(
        action_type=clamp_action(decision.action_type),
        summary=decision.summary,
    )
