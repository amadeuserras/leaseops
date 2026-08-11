from __future__ import annotations

from datetime import UTC, datetime, timedelta

from leaseops.db.models import Email, Run
from leaseops.models.enums import EmailStatus, RunStatus


async def test_get_latest_run_email_id(api_client, db_session, demo_session) -> None:
    older = Email(
        session_id=demo_session.id,
        sender="a@example.com",
        subject="Older",
        body="body",
        received_at=datetime.now(UTC),
        status=EmailStatus.PENDING,
    )
    newer = Email(
        session_id=demo_session.id,
        sender="b@example.com",
        subject="Newer",
        body="body",
        received_at=datetime.now(UTC),
        status=EmailStatus.PENDING,
    )
    db_session.add_all([older, newer])
    await db_session.commit()
    await db_session.refresh(older)
    await db_session.refresh(newer)

    now = datetime.now(UTC)
    db_session.add_all(
        [
            Run(
                email_id=older.id,
                status=RunStatus.DONE,
                started_at=now - timedelta(hours=1),
                ended_at=now - timedelta(minutes=50),
            ),
            Run(
                email_id=newer.id,
                status=RunStatus.DONE,
                started_at=now,
                ended_at=now,
            ),
        ]
    )
    await db_session.commit()

    response = await api_client.get("/runs/latest")
    assert response.status_code == 200
    assert response.json()["email_id"] == str(newer.id)


async def test_get_latest_run_empty(api_client) -> None:
    response = await api_client.get("/runs/latest")
    assert response.status_code == 200
    assert response.json()["email_id"] is None
