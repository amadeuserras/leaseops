from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from leaseops.api.deps import SessionDep
from leaseops.api.schemas import SessionResponse
from leaseops.db import demo_sessions as demo_sessions_repo

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session: SessionDep) -> SessionResponse:
    demo = await demo_sessions_repo.create_demo_session(session)
    return SessionResponse(id=demo.id)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID, session: SessionDep) -> SessionResponse:
    demo = await demo_sessions_repo.get_demo_session(session, session_id)
    if demo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="session not found"
        )
    return SessionResponse(id=demo.id)
