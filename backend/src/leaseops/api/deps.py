from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db import demo_sessions as demo_sessions_repo
from leaseops.db.models import DemoSession
from leaseops.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def require_demo_session(
    session: SessionDep,
    x_session_id: Annotated[UUID | None, Header()] = None,
) -> DemoSession:
    if x_session_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id header is required",
        )
    demo = await demo_sessions_repo.get_demo_session(session, x_session_id)
    if demo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session not found",
        )
    return demo


DemoSessionDep = Annotated[DemoSession, Depends(require_demo_session)]
