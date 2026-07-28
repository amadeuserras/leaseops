from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.agent.runner import GraphRunner
from leaseops.db import emails as emails_repo
from leaseops.db.session import get_session
from leaseops.models.schemas import RunCreate, RunResponse

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
