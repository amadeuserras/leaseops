from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.db.models import DemoSession, Email
from leaseops.demo.inbox_template import load_inbox_template


async def get_demo_session(
    session: AsyncSession, session_id: UUID
) -> DemoSession | None:
    return await session.get(DemoSession, session_id)


async def create_empty_session(session: AsyncSession) -> DemoSession:
    demo = DemoSession()
    session.add(demo)
    await session.commit()
    await session.refresh(demo)
    return demo


async def create_demo_session(session: AsyncSession) -> DemoSession:
    """Mint a visitor session and clone a fresh inbox into it."""
    demo = DemoSession()
    session.add(demo)
    await session.flush()

    session.add_all(
        [
            Email(
                session_id=demo.id,
                sender=row["sender"],
                subject=row["subject"],
                body=row["body"],
                received_at=row["received_at"],
                status=row["status"],
            )
            for row in load_inbox_template()
        ]
    )
    await session.commit()
    await session.refresh(demo)
    return demo


async def session_owns_email(
    session: AsyncSession, *, session_id: UUID, email_id: UUID
) -> bool:
    return (
        await session.scalar(
            select(Email.id).where(
                Email.id == email_id,
                Email.session_id == session_id,
            )
        )
    ) is not None
