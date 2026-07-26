from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import Email


async def get_email_by_id(session: AsyncSession, email_id: UUID) -> Email | None:
    return await session.get(Email, email_id)


async def get_latest_email_by_sender(
    session: AsyncSession, sender: str
) -> Email | None:
    result = await session.scalars(
        select(Email)
        .where(Email.sender == sender)
        .order_by(Email.received_at.desc())
        .limit(1)
    )
    return result.first()
