from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import UUID

from leaseops.agent.enums import PlanAction
from leaseops.agent.events import (
    CostEvent,
    ErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StreamEventAdapter,
)
from leaseops.agent.runner import GraphRunner
from leaseops.agent.runtime import graph_runner
from leaseops.agent.state import AgentState
from leaseops.api.schemas import EmailCreate
from leaseops.core.config import settings
from leaseops.db import emails as emails_repo
from leaseops.db.session import open_session, use_database
from leaseops.evals.schemas import CaseResult, GoldenItem
from leaseops.evals.score import score
from leaseops.evals.writes import load_performed_actions
from leaseops.models.enums import RunStatus

CaseProgress = Callable[[int, int, GoldenItem], Awaitable[None]]


async def _run_graph(
    item: GoldenItem,
    runner: GraphRunner,
) -> tuple[AgentState, list[PlanAction], list[PlanAction], float, float]:
    email_payload = item.email

    async with open_session() as session:
        email = await emails_repo.create_email(
            session,
            EmailCreate(
                sender=email_payload.sender,
                subject=email_payload.subject,
                body=email_payload.body,
                received_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        )

        t0 = time.monotonic()
        total_cost = 0.0
        run_id: UUID | None = None
        paused = False

        async for raw in runner.stream(session, email):
            event = StreamEventAdapter.validate_python(raw)
            if isinstance(event, RunStartedEvent):
                run_id = UUID(event.run_id)
            elif isinstance(event, CostEvent):
                total_cost += event.cost_usd
            elif isinstance(event, ErrorEvent):
                raise RuntimeError(event.message)
            elif isinstance(event, RunFinishedEvent):
                paused = event.status == RunStatus.PAUSED

        if run_id is None:
            raise RuntimeError("graph stream did not emit run_started")

        returned_before = await load_performed_actions(session, email.id)

        if paused:
            await runner.approve(session, run_id)

        returned_after = await load_performed_actions(session, email.id)

        latency_s = time.monotonic() - t0
        snapshot = await runner.graph.aget_state(
            {"configurable": {"thread_id": str(run_id)}}
        )
        state = AgentState.model_validate(snapshot.values)
        return state, returned_before, returned_after, total_cost, latency_s


async def _run_case(item: GoldenItem, runner: GraphRunner) -> CaseResult:
    state, returned_before, returned_after, cost_usd, latency_s = await _run_graph(
        item, runner
    )
    return score(
        item,
        state,
        returned_before,
        returned_after,
        cost_usd,
        latency_s,
    )


async def run_cases(
    items: list[GoldenItem],
    *,
    on_start: CaseProgress | None = None,
    on_done: CaseProgress | None = None,
) -> list[CaseResult]:
    async with (
        use_database(settings.evals_database_url),
        graph_runner() as runner,
    ):
        results: list[CaseResult] = []
        n = len(items)
        for i, item in enumerate(items, 1):
            if on_start is not None:
                await on_start(i, n, item)
            results.append(await _run_case(item, runner))
            if on_done is not None:
                await on_done(i, n, item)
        return results
