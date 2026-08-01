from __future__ import annotations

from dataclasses import dataclass

from leaseops.agent.state import (
    AgentState,
    EmailCategory,
    PlanAction,
    Responsibility,
)


@dataclass(frozen=True)
class _PlanResult:
    actions: list[PlanAction]


def plan(state: AgentState) -> _PlanResult:
    if state.category == EmailCategory.EMERGENCY:
        return _PlanResult(
            actions=[PlanAction.CALL_TENANT, PlanAction.SEND_REPLY],
        )

    actions = [PlanAction.SEND_REPLY]
    if (
        state.category == EmailCategory.MAINTENANCE
        and state.responsibility == Responsibility.LANDLORD
    ):
        actions.append(PlanAction.CREATE_WORK_ORDER)
    return _PlanResult(actions=actions)
