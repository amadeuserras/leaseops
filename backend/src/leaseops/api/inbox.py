from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from leaseops.api.deps import DemoSessionDep, SessionDep
from leaseops.api.schemas import EmailCreate, EmailListResponse, EmailResponse
from leaseops.db import emails as repo
from leaseops.db import runs as runs_repo
from leaseops.db.emails import InboxRow
from leaseops.models.enums import EmailStatus

router = APIRouter(prefix="/inbox", tags=["inbox"])


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
    demo: DemoSessionDep,
) -> EmailResponse:
    email = await repo.create_email(session, payload, session_id=demo.id)
    return _to_response(InboxRow(email=email))


@router.get("", response_model=EmailListResponse)
async def list_inbox(
    session: SessionDep,
    demo: DemoSessionDep,
    status_filter: Annotated[EmailStatus | None, Query(alias="status")] = None,
) -> EmailListResponse:
    rows = await repo.list_inbox_rows(session, session_id=demo.id, status=status_filter)
    return EmailListResponse(
        items=[_to_response(row) for row in rows],
        agent_last_ran_at=await runs_repo.get_agent_last_ran_at(
            session, session_id=demo.id
        ),
    )


@router.get("/{email_id}", response_model=EmailResponse)
async def get_inbox_email(
    email_id: UUID,
    session: SessionDep,
    demo: DemoSessionDep,
) -> EmailResponse:
    row = await repo.get_inbox_row(session, email_id, session_id=demo.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="email not found"
        )
    return _to_response(row)
