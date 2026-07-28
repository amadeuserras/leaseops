from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select

from leaseops.db.models import Email, Outbox
from leaseops.db.outbox import create_outbox_entry
from leaseops.models.schemas import EmailStatus, OutboxCreate


async def test_outbox_create_is_idempotent_for_same_email(db_session) -> None:
    email = Email(
        sender="tenant@example.com",
        subject="Lease question",
        body="Can I paint the walls?",
        received_at=datetime.now(UTC),
        status=EmailStatus.PENDING,
    )
    db_session.add(email)
    await db_session.commit()

    payload = OutboxCreate(
        email_id=email.id,
        draft_text="Thanks for asking about painting.",
    )
    await create_outbox_entry(db_session, payload)
    await create_outbox_entry(db_session, payload)

    count = await db_session.scalar(
        select(func.count()).select_from(Outbox).where(Outbox.email_id == email.id)
    )
    assert count == 1
