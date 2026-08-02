from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db import emails as repo
from leaseops.db import runs as runs_repo
from leaseops.db.emails import InboxRow
from leaseops.db.session import get_session
from leaseops.models.enums import EmailStatus
from leaseops.models.schemas import EmailCreate, EmailListResponse, EmailResponse

router = APIRouter(prefix="/inbox", tags=["inbox"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _to_response(row: InboxRow) -> EmailResponse:
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


@router.post("", response_model=EmailResponse, status_code=status.HTTP_201_CREATED)
async def create_email(
    payload: EmailCreate,
    session: SessionDep,
) -> EmailResponse:
    email = await repo.create_email(session, payload)
    return _to_response(InboxRow(email=email))


@router.get("", response_model=EmailListResponse)
async def list_inbox(
    session: SessionDep,
    status_filter: Annotated[EmailStatus | None, Query(alias="status")] = None,
) -> EmailListResponse:
    rows = await repo.list_inbox_rows(session, status=status_filter)
    return EmailListResponse(
        items=[_to_response(row) for row in rows],
        agent_last_ran_at=await runs_repo.get_agent_last_ran_at(session),
    )


@router.get("/{email_id}", response_model=EmailResponse)
async def get_inbox_email(
    email_id: UUID,
    session: SessionDep,
) -> EmailResponse:
    row = await repo.get_inbox_row(session, email_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="email not found"
        )
    return _to_response(row)
