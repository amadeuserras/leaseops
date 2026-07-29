from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db import emails as repo
from leaseops.db.session import get_session
from leaseops.models.enums import EmailStatus
from leaseops.models.schemas import EmailCreate, EmailListResponse, EmailResponse

router = APIRouter(prefix="/inbox", tags=["inbox"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=EmailResponse, status_code=status.HTTP_201_CREATED)
async def create_email(
    payload: EmailCreate,
    session: SessionDep,
) -> EmailResponse:
    email = await repo.create_email(session, payload)
    return EmailResponse.model_validate(email)


@router.get("", response_model=EmailListResponse)
async def list_inbox(
    session: SessionDep,
    status_filter: Annotated[EmailStatus | None, Query(alias="status")] = None,
) -> EmailListResponse:
    items = await repo.list_emails(session, status=status_filter)
    return EmailListResponse(
        items=[EmailResponse.model_validate(item) for item in items]
    )


@router.get("/{email_id}", response_model=EmailResponse)
async def get_inbox_email(
    email_id: UUID,
    session: SessionDep,
) -> EmailResponse:
    email = await repo.get_email_by_id(session, email_id)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="email not found"
        )
    return EmailResponse.model_validate(email)
