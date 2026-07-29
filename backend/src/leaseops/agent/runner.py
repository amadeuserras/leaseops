from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass
from typing import Any, cast
from uuid import UUID

from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.agent.approval import ApprovalDecision, ApprovalRequest
from leaseops.agent.state import AgentState
from leaseops.db import runs as runs_repo
from leaseops.db.models import Email, Run
from leaseops.models.schemas import RunStatus


@dataclass(frozen=True)
class PendingApproval:
    run_id: UUID
    request: ApprovalRequest


@dataclass
class GraphRunner:
    graph: Any

    async def start(self, session: AsyncSession, email: Email) -> Run:
        run = await runs_repo.create_run(session, email.id)
        config = self._thread_config(run.id)
        initial = AgentState(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            body=email.body,
        )
        await self.graph.ainvoke(initial, config)
        snapshot = await self.graph.aget_state(config)
        if snapshot.interrupts:
            return await runs_repo.set_run_status(session, run, RunStatus.PAUSED)
        return await runs_repo.set_run_status(session, run, RunStatus.DONE, ended=True)

    async def stream(
        self, session: AsyncSession, email: Email
    ) -> AsyncGenerator[dict[str, Any]]:
        run = await runs_repo.create_run(session, email.id)
        config = self._thread_config(run.id)
        initial = AgentState(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            body=email.body,
        )
        yield {"type": "run_started", "run_id": str(run.id)}

        paused = False
        try:
            async for mode, chunk in self.graph.astream(
                initial, config, stream_mode=["tasks", "custom"]
            ):
                if mode == "custom":
                    yield cast(dict[str, Any], chunk)
                    continue
                task = cast(dict[str, Any], chunk)
                node = cast(str, task["name"])
                if "result" not in task:
                    yield {"type": "node_started", "node": node}
                    continue
                interrupts = cast(list[dict[str, Any]], task["interrupts"])
                if interrupts:
                    paused = True
                    request = ApprovalRequest(**interrupts[0]["value"])
                    yield {"type": "paused", "request": asdict(request)}
                    continue
                yield {"type": "node_finished", "node": node, "output": task["result"]}
        except Exception as exc:
            await runs_repo.set_run_status(session, run, RunStatus.FAILED, ended=True)
            yield {"type": "error", "message": str(exc)}
            return

        status = RunStatus.PAUSED if paused else RunStatus.DONE
        run = await runs_repo.set_run_status(session, run, status, ended=not paused)
        yield {"type": "run_finished", "status": status.value}

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
            ApprovalDecision(approved=True),
        )

    async def reject(
        self,
        session: AsyncSession,
        run_id: UUID,
        rejection_reason: str | None,
    ) -> Run:
        return await self._decide(
            session,
            run_id,
            ApprovalDecision(approved=False, rejection_reason=rejection_reason),
        )

    async def _decide(
        self,
        session: AsyncSession,
        run_id: UUID,
        decision: ApprovalDecision,
    ) -> Run:
        run = await runs_repo.get_run(session, run_id)
        if run is None:
            raise LookupError("run not found")
        if run.status != RunStatus.PAUSED:
            raise RuntimeError("run is not waiting for approval")

        config = self._thread_config(run_id)
        try:
            await self.graph.ainvoke(
                Command(resume=asdict(decision)),
                config,
            )
        except Exception:
            await runs_repo.set_run_status(session, run, RunStatus.FAILED, ended=True)
            raise
        return await runs_repo.set_run_status(session, run, RunStatus.DONE, ended=True)

    async def _pending_request(self, run_id: UUID) -> ApprovalRequest | None:
        snapshot = await self.graph.aget_state(self._thread_config(run_id))
        if not snapshot.interrupts:
            return None
        raw = cast(dict[str, Any], snapshot.interrupts[0].value)
        return ApprovalRequest(**raw)

    @staticmethod
    def _thread_config(run_id: UUID) -> dict[str, Any]:
        return {"configurable": {"thread_id": str(run_id)}}
