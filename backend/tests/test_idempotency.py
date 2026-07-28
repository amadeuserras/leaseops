from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select

from leaseops.db.models import Email, Outbox, Tenant, WorkOrder
from leaseops.db.outbox import create_outbox_entry
from leaseops.db.work_orders import create_work_order
from leaseops.models.schemas import EmailStatus, OutboxCreate, WorkOrderCreate


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


async def test_work_order_create_is_idempotent_for_same_email(db_session) -> None:
    tenant = Tenant(
        email="tenant@example.com",
        name="Test Tenant",
        document_id=uuid4(),
        address="1 Test St",
    )
    db_session.add(tenant)
    await db_session.flush()

    email = Email(
        sender="tenant@example.com",
        subject="Leaky faucet",
        body="Kitchen sink is dripping.",
        received_at=datetime.now(UTC),
        status=EmailStatus.PENDING,
    )
    db_session.add(email)
    await db_session.commit()

    payload = WorkOrderCreate(
        email_id=email.id,
        tenant_id=tenant.id,
        issue="Kitchen sink drip",
    )
    await create_work_order(db_session, payload)
    await create_work_order(db_session, payload)

    count = await db_session.scalar(
        select(func.count())
        .select_from(WorkOrder)
        .where(WorkOrder.email_id == email.id)
    )
    assert count == 1
