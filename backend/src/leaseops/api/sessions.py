from __future__ import annotations

from fastapi import APIRouter, status

from leaseops.api.deps import SessionDep
from leaseops.api.schemas import SessionResponse
from leaseops.db import demo_sessions as demo_sessions_repo

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session: SessionDep) -> SessionResponse:
    demo = await demo_sessions_repo.create_demo_session(session)
    return SessionResponse(id=demo.id)
