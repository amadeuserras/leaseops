from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import Tenant


async def get_tenant_by_email(session: AsyncSession, email: str) -> Tenant | None:
    normalized = email.strip().lower()
    stmt = select(Tenant).where(Tenant.email == normalized)
    return await session.scalar(stmt)
