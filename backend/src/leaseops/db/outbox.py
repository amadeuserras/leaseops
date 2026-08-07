from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.api.schemas import OutboxCreate
from leaseops.db.models import Outbox


async def create_outbox_entry(session: AsyncSession, payload: OutboxCreate) -> Outbox:
    await session.execute(
        insert(Outbox)
        .values(
            email_id=payload.email_id,
            draft_text=payload.draft_text,
            status=payload.status,
        )
        .on_conflict_do_nothing(index_elements=["email_id"])
    )
    await session.commit()
    result = await session.scalars(
        select(Outbox).where(Outbox.email_id == payload.email_id)
    )
    return result.one()


async def list_outbox_by_email_id(
    session: AsyncSession, email_id: UUID
) -> list[Outbox]:
    result = await session.scalars(select(Outbox).where(Outbox.email_id == email_id))
    return list(result.all())
