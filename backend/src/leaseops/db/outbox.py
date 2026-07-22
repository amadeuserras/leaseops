from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import Outbox
from leaseops.models.schemas import OutboxCreate


async def create_outbox_entry(session: AsyncSession, payload: OutboxCreate) -> Outbox:
    entry = Outbox(
        email_id=payload.email_id,
        draft_text=payload.draft_text,
        status=payload.status,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry
