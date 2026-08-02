from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.agent.runner import GraphRunner
from leaseops.api.schemas import (
    ApprovalListResponse,
    ApprovalRequestResponse,
    RunResponse,
)
from leaseops.db.session import get_session

router = APIRouter(prefix="/approvals", tags=["approvals"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_runner(request: Request) -> GraphRunner:
    return request.app.state.runner


RunnerDep = Annotated[GraphRunner, Depends(get_runner)]


@router.get("", response_model=ApprovalListResponse)
async def list_pending_approvals(
    session: SessionDep,
    runner: RunnerDep,
) -> ApprovalListResponse:
    pending = await runner.list_pending(session)
    return ApprovalListResponse(
        items=[
            ApprovalRequestResponse(
                run_id=item.run_id,
                email_id=item.request.email_id,
                category=item.request.category,
                severity=item.request.severity,
                received_at=item.request.received_at,
                tenant_name=item.request.tenant_name,
                unit=item.request.unit,
                address=item.request.address,
                issue_summary=item.request.issue_summary,
                appliance_or_system=item.request.appliance_or_system,
                responsibility=item.request.responsibility,
                citation=item.request.citation,
                original_email=item.request.original_email,
                draft=item.request.draft,
                actions=item.request.actions,
            )
            for item in pending
        ]
    )


@router.post("/{run_id}/approve", response_model=RunResponse)
async def approve_run(
    run_id: UUID,
    session: SessionDep,
    runner: RunnerDep,
) -> RunResponse:
    try:
        run = await runner.approve(session, run_id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="run not found"
        ) from None
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from None
    return RunResponse.model_validate(run)


@router.post("/{run_id}/reject", response_model=RunResponse)
async def reject_run(
    run_id: UUID,
    session: SessionDep,
    runner: RunnerDep,
) -> RunResponse:
    try:
        run = await runner.reject(session, run_id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="run not found"
        ) from None
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from None
    return RunResponse.model_validate(run)
