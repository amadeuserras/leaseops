from __future__ import annotations

from leaseops.agent.schemas import PlanOutput
from leaseops.agent.state import (
    AgentState,
    EmailCategory,
    PlanAction,
    Responsibility,
)


def plan(state: AgentState) -> PlanOutput:
    if state.category == EmailCategory.EMERGENCY:
        return PlanOutput(actions=[PlanAction.SEND_REPLY])

    actions = [PlanAction.SEND_REPLY]
    if (
        state.category == EmailCategory.MAINTENANCE
        and state.responsibility == Responsibility.LANDLORD
    ):
        actions.append(PlanAction.CREATE_WORK_ORDER)
    return PlanOutput(actions=actions)
