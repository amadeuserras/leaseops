from __future__ import annotations

from leaseops.agent.state import AgentState


async def execute(state: AgentState) -> None:
    print(state.actions)
