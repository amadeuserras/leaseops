from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from leaseops.agent.runner import GraphRunner
from leaseops.agent.schemas import StepResponse, StepResponseAdapter
from leaseops.api.deps import DemoSessionDep, SessionDep
from leaseops.api.schemas import (
    EmailResponse,
    LatestRunResponse,
    RunCreate,
    RunDetailResponse,
    RunResponse,
    RunStats,
)
from leaseops.db import emails as emails_repo
from leaseops.db import runs as runs_repo
from leaseops.db import steps as steps_repo
from leaseops.db.emails import InboxRow
from leaseops.db.models import Run, Step

router = APIRouter(prefix="/runs", tags=["runs"])


def get_runner(request: Request) -> GraphRunner:
    return request.app.state.runner


RunnerDep = Annotated[GraphRunner, Depends(get_runner)]


def _email_response(row: InboxRow) -> EmailResponse:
    email = row.email
    return EmailResponse(
        id=email.id,
        sender=email.sender,
        subject=email.subject,
        body=email.body,
        received_at=email.received_at,
        status=email.status,
        unit=row.unit,
        severity=row.severity,
        actions_taken=row.actions_taken,
    )


def _step_responses(steps: list[Step]) -> list[StepResponse]:
    return [
        StepResponseAdapter.validate_python(
            {
                "id": s.id,
                "run_id": s.run_id,
                "node_name": s.node_name,
                "output": s.output,
                "model": s.model,
                "input_tokens": s.input_tokens,
                "output_tokens": s.output_tokens,
                "cost_usd": float(s.cost_usd) if s.cost_usd is not None else None,
                "created_at": s.created_at,
            }
        )
        for s in steps
    ]


def _stats(run: Run | None, steps: list[Step]) -> RunStats:
    if run is None:
        return RunStats()
    return RunStats.model_validate(runs_repo.run_aggregates(run, steps))


@router.get("/latest", response_model=LatestRunResponse)
async def get_latest_run(
    session: SessionDep, demo: DemoSessionDep
) -> LatestRunResponse:
    run = await runs_repo.get_latest_run(session, session_id=demo.id)
    return LatestRunResponse(email_id=run.email_id if run is not None else None)


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def start_run(
    payload: RunCreate,
    session: SessionDep,
    demo: DemoSessionDep,
    runner: RunnerDep,
) -> RunResponse:
    email = await emails_repo.get_email_by_id(
        session, payload.email_id, session_id=demo.id
    )
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="email not found"
        )
    run = await runner.start(session, email)
    return RunResponse.model_validate(run)


def _sse(event: dict[str, object]) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


@router.post("/stream")
async def stream_run(
    payload: RunCreate,
    session: SessionDep,
    demo: DemoSessionDep,
    runner: RunnerDep,
) -> StreamingResponse:
    email = await emails_repo.get_email_by_id(
        session, payload.email_id, session_id=demo.id
    )
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="email not found"
        )

    async def event_source() -> AsyncGenerator[str]:
        async for event in runner.stream(session, email):
            yield _sse(event)

    return StreamingResponse(event_source(), media_type="text/event-stream")


@router.post("/rerun/stream")
async def rerun_stream(
    payload: RunCreate,
    session: SessionDep,
    demo: DemoSessionDep,
    runner: RunnerDep,
) -> StreamingResponse:
    email = await emails_repo.get_email_by_id(
        session, payload.email_id, session_id=demo.id
    )
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="email not found"
        )
    await runner.wipe(session, email.id)

    async def event_source() -> AsyncGenerator[str]:
        async for event in runner.stream(session, email):
            yield _sse(event)

    return StreamingResponse(event_source(), media_type="text/event-stream")


@router.get("/{email_id}", response_model=RunDetailResponse)
async def get_run(
    email_id: UUID, session: SessionDep, demo: DemoSessionDep
) -> RunDetailResponse:
    row = await emails_repo.get_inbox_row(session, email_id, session_id=demo.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="email not found"
        )
    run = await runs_repo.get_run_by_email_id(session, email_id)
    steps = (
        await steps_repo.list_steps_for_run(session, run.id) if run is not None else []
    )
    return RunDetailResponse(
        email=_email_response(row),
        steps=_step_responses(steps),
        stats=_stats(run, steps),
    )
