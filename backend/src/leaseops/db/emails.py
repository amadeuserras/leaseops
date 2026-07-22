from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import Email


async def get_email_by_id(session: AsyncSession, email_id: UUID) -> Email | None:
    return await session.get(Email, email_id)
