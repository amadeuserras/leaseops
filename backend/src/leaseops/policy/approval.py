from __future__ import annotations

from typing import TypeGuard

from leaseops.agent.state import ActionType

# Actions that write to a system of record. Every one of them needs a human yes.
GATED_ACTIONS: frozenset[ActionType] = frozenset(
    {ActionType.CREATE_WORK_ORDER, ActionType.SEND_REPLY}
)


def requires_approval(action: ActionType | None) -> TypeGuard[ActionType]:
    return action in GATED_ACTIONS
