from __future__ import annotations

from leaseops.agent.state import ActionType

ALLOWED_ACTIONS: frozenset[ActionType] = frozenset(ActionType)


def clamp_action(action: ActionType) -> ActionType:
    if action not in ALLOWED_ACTIONS:
        return ActionType.ESCALATE
    return action
