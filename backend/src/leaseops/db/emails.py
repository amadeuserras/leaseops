from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import Email
from leaseops.models.schemas import EmailCreate, EmailStatus


async def create_email(session: AsyncSession, payload: EmailCreate) -> Email:
    email = Email(
        sender=payload.sender,
        subject=payload.subject,
        body=payload.body,
        received_at=payload.received_at,
        status=payload.status,
    )
    session.add(email)
    await session.commit()
    await session.refresh(email)
    return email


async def list_emails(
    session: AsyncSession, *, status: EmailStatus | None = None
) -> list[Email]:
    stmt = select(Email).order_by(Email.received_at.desc())
    if status is not None:
        stmt = stmt.where(Email.status == status)
    return list((await session.scalars(stmt)).all())


async def get_email_by_id(session: AsyncSession, email_id: UUID) -> Email | None:
    return await session.get(Email, email_id)


async def get_email_by_subject(session: AsyncSession, subject: str) -> Email | None:
    result = await session.scalars(
        select(Email)
        .where(Email.subject == subject)
        .order_by(Email.received_at.desc())
        .limit(1)
    )
    return result.first()
