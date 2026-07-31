from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.agent.runner import GraphRunner
from leaseops.db import emails as emails_repo
from leaseops.db import steps as steps_repo
from leaseops.db.session import SessionLocal, get_session
from leaseops.models.schemas import (
    RunCreate,
    RunResponse,
    StepListResponse,
    StepResponse,
)

router = APIRouter(prefix="/runs", tags=["runs"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_runner(request: Request) -> GraphRunner:
    return request.app.state.runner


RunnerDep = Annotated[GraphRunner, Depends(get_runner)]


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def start_run(
    payload: RunCreate,
    session: SessionDep,
    runner: RunnerDep,
) -> RunResponse:
    email = await emails_repo.get_email_by_id(session, payload.email_id)
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
    runner: RunnerDep,
) -> StreamingResponse:
    email = await emails_repo.get_email_by_id(session, payload.email_id)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="email not found"
        )

    async def event_source() -> AsyncGenerator[str]:
        async with SessionLocal() as stream_session:
            async for event in runner.stream(stream_session, email):
                yield _sse(event)

    return StreamingResponse(event_source(), media_type="text/event-stream")


@router.get("/{email_id}/steps", response_model=StepListResponse)
async def list_steps(email_id: UUID, session: SessionDep) -> StepListResponse:
    steps = await steps_repo.list_steps_by_email(session, email_id)
    return StepListResponse(items=[StepResponse.model_validate(s) for s in steps])
