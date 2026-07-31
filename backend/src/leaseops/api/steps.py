from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db import steps as steps_repo
from leaseops.db.session import get_session
from leaseops.models.schemas import StepListResponse, StepResponse

router = APIRouter(prefix="/steps", tags=["steps"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=StepListResponse)
async def list_steps(email_id: UUID, session: SessionDep) -> StepListResponse:
    steps = await steps_repo.list_steps_by_email(session, email_id)
    return StepListResponse(items=[StepResponse.model_validate(s) for s in steps])
