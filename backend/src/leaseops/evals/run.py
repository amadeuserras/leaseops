from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver

from leaseops.agent.checkpoint import CHECKPOINT_SERDE
from leaseops.agent.graph import build_graph
from leaseops.agent.state import AgentState
from leaseops.evals.schemas import CaseResult, GoldenItem
from leaseops.evals.score import score


async def _run_graph(
    item: GoldenItem,
    graph: Any,
) -> tuple[AgentState, float, float]:
    email = item.email
    config = {"configurable": {"thread_id": str(uuid4())}}
    initial = AgentState(
        email_id=uuid4(),
        sender=email.sender,
        subject=email.subject,
        body=email.body,
        received_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    total_cost = 0.0
    t0 = time.monotonic()

    async for chunk in graph.astream(initial, config, stream_mode="custom"):
        event = cast(dict[str, object], chunk)
        if event.get("type") == "cost":
            total_cost += float(cast(float | int | str, event.get("cost_usd", 0.0)))

    latency_s = time.monotonic() - t0
    snapshot = await graph.aget_state(config)
    state = AgentState.model_validate(snapshot.values)
    return state, total_cost, latency_s


async def _run_case(item: GoldenItem, graph: Any) -> CaseResult:
    state, cost_usd, latency_s = await _run_graph(item, graph)
    return score(item, state, cost_usd, latency_s)


async def run_cases(items: list[GoldenItem]) -> list[CaseResult]:
    graph = build_graph(checkpointer=InMemorySaver(serde=CHECKPOINT_SERDE))
    return [await _run_case(item, graph) for item in items]
