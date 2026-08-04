from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict, cast
from uuid import UUID

from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.agent.events import (
    CostEvent,
    CustomEventAdapter,
    ErrorEvent,
    NodeFinishedEvent,
    NodeStartedEvent,
    PausedEvent,
    RunFinishedEvent,
    RunStartedEvent,
)
from leaseops.agent.state import AgentState
from leaseops.agent.step_schemas import (
    ApprovalCard,
    ApprovalOutput,
    ExecuteOutput,
    parse_node_name,
    parse_step_output,
)
from leaseops.db import emails as emails_repo
from leaseops.db import runs as runs_repo
from leaseops.db import steps as steps_repo
from leaseops.db.models import Email, Run
from leaseops.models.enums import EmailStatus, RunStatus


class TaskChunk(TypedDict):
    id: str
    name: str
    error: NotRequired[Any | None]
    result: NotRequired[Any]
    interrupts: NotRequired[list[dict[str, Any]]]
    input: NotRequired[Any]
    triggers: NotRequired[list[str]]


def _add_cost(existing: CostEvent | None, incoming: CostEvent) -> CostEvent:
    if existing is None:
        return incoming
    return CostEvent(
        node=incoming.node,
        model=incoming.model,
        input_tokens=existing.input_tokens + incoming.input_tokens,
        output_tokens=existing.output_tokens + incoming.output_tokens,
        cost_usd=existing.cost_usd + incoming.cost_usd,
    )


@dataclass(frozen=True)
class PendingApproval:
    run_id: UUID
    request: ApprovalCard


@dataclass
class GraphRunner:
    graph: Any

    async def start(self, session: AsyncSession, email: Email) -> Run:
        run = await runs_repo.create_run(session, email.id)
        await emails_repo.set_email_status(session, email.id, EmailStatus.PROCESSING)
        config = self._thread_config(run.id)
        initial = AgentState(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            body=email.body,
            received_at=email.received_at,
        )
        await self.graph.ainvoke(initial, config)
        snapshot = await self.graph.aget_state(config)
        if snapshot.interrupts:
            await emails_repo.set_email_status(
                session, email.id, EmailStatus.AWAITING_APPROVAL
            )
            return await runs_repo.set_run_status(session, run, RunStatus.PAUSED)
        return await runs_repo.set_run_status(session, run, RunStatus.DONE, ended=True)

    async def stream(
        self, session: AsyncSession, email: Email
    ) -> AsyncGenerator[dict[str, Any]]:
        run = await runs_repo.create_run(session, email.id)
        await emails_repo.set_email_status(session, email.id, EmailStatus.PROCESSING)
        config = self._thread_config(run.id)
        initial = AgentState(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            body=email.body,
            received_at=email.received_at,
        )
        yield RunStartedEvent(run_id=str(run.id)).model_dump(mode="json")

        paused = False
        cost_by_node: dict[str, CostEvent] = {}
        try:
            async for pair in self.graph.astream(
                initial, config, stream_mode=["tasks", "custom"]
            ):
                mode = pair[0]
                chunk = pair[1]

                # Custom Chunks: written by emit (cost, tool calls, tool results)
                if mode == "custom":
                    custom = CustomEventAdapter.validate_python(chunk)
                    if custom.type == "cost":
                        cost_by_node[custom.node] = _add_cost(
                            cost_by_node.get(custom.node), custom
                        )
                    yield custom.model_dump(mode="json")
                    continue

                # Task chunks: written by the graph (node start / finished / pause)
                task_chunk = cast(TaskChunk, chunk)
                node_name = task_chunk["name"]

                # Node started: write the start event
                if "result" not in task_chunk:
                    yield NodeStartedEvent(node=node_name).model_dump(mode="json")
                    continue

                # Node failed: LangGraph still sends result={} with error set
                error = task_chunk.get("error")
                if error is not None:
                    raise error

                # Node paused: write the pause event & update status
                interrupts = task_chunk.get("interrupts") or []
                if interrupts:
                    paused = True
                    await emails_repo.set_email_status(
                        session, email.id, EmailStatus.AWAITING_APPROVAL
                    )
                    request = ApprovalCard.model_validate(interrupts[0]["value"])
                    await steps_repo.create_step(
                        session,
                        run_id=run.id,
                        node_name=parse_node_name(node_name),
                        output=request,
                    )
                    yield PausedEvent(request=request).model_dump(mode="json")
                    continue

                # Node finished: write the finished event & create the step
                cost = cost_by_node.pop(node_name, None)
                parsed_name = parse_node_name(node_name)
                await steps_repo.create_step(
                    session,
                    run_id=run.id,
                    node_name=parsed_name,
                    output=parse_step_output(parsed_name, task_chunk["result"]),
                    model=cost.model if cost is not None else None,
                    input_tokens=cost.input_tokens if cost is not None else None,
                    output_tokens=cost.output_tokens if cost is not None else None,
                    cost_usd=cost.cost_usd if cost is not None else None,
                )
                yield NodeFinishedEvent(
                    node=node_name, output=task_chunk["result"]
                ).model_dump(mode="json")

        # Error: write the error event & update status
        except Exception as exc:
            await runs_repo.set_run_status(session, run, RunStatus.FAILED, ended=True)
            yield ErrorEvent(message=str(exc)).model_dump(mode="json")
            return

        # Done: update the run status
        status = RunStatus.PAUSED if paused else RunStatus.DONE
        run = await runs_repo.set_run_status(session, run, status, ended=not paused)
        yield RunFinishedEvent(status=status.value).model_dump(mode="json")

    async def list_pending(self, session: AsyncSession) -> list[PendingApproval]:
        paused = await runs_repo.list_runs(session, status=RunStatus.PAUSED)
        pending: list[PendingApproval] = []
        for run in paused:
            request = await self._pending_request(run.id)
            if request is None:
                continue
            pending.append(PendingApproval(run_id=run.id, request=request))
        return pending

    async def approve(self, session: AsyncSession, run_id: UUID) -> Run:
        return await self._decide(
            session,
            run_id,
            ApprovalOutput(approved=True),
        )

    async def reject(self, session: AsyncSession, run_id: UUID) -> Run:
        return await self._decide(
            session,
            run_id,
            ApprovalOutput(approved=False),
        )

    async def _decide(
        self,
        session: AsyncSession,
        run_id: UUID,
        decision: ApprovalOutput,
    ) -> Run:
        run = await runs_repo.get_run(session, run_id)
        if run is None:
            raise LookupError("run not found")
        if run.status != RunStatus.PAUSED:
            raise RuntimeError("run is not waiting for approval")

        if decision.approved:
            await emails_repo.set_email_status(
                session, run.email_id, EmailStatus.PROCESSING
            )

        config = self._thread_config(run_id)
        try:
            state = AgentState.model_validate(
                await self.graph.ainvoke(
                    Command(resume=decision.model_dump()),
                    config,
                )
            )
        except Exception:
            await runs_repo.set_run_status(session, run, RunStatus.FAILED, ended=True)
            raise

        if decision.approved:
            await steps_repo.create_step(
                session,
                run_id=run.id,
                node_name="execute",
                output=ExecuteOutput(succeeded=state.succeeded),
            )
        await emails_repo.set_email_status(session, run.email_id, EmailStatus.PROCESSED)
        return await runs_repo.set_run_status(session, run, RunStatus.DONE, ended=True)

    async def _pending_request(self, run_id: UUID) -> ApprovalCard | None:
        snapshot = await self.graph.aget_state(self._thread_config(run_id))
        if not snapshot.interrupts:
            return None
        raw = cast(dict[str, Any], snapshot.interrupts[0].value)
        return ApprovalCard.model_validate(raw)

    @staticmethod
    def _thread_config(run_id: UUID) -> dict[str, Any]:
        return {"configurable": {"thread_id": str(run_id)}}
