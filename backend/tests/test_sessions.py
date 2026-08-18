from __future__ import annotations

from datetime import UTC, datetime

from leaseops.db import demo_sessions as demo_sessions_repo
from leaseops.db.models import Email
from leaseops.models.enums import EmailStatus


async def test_get_session_returns_404_when_missing(api_client) -> None:
    response = await api_client.get("/sessions/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 404


async def test_create_session_clones_inbox(api_client) -> None:
    response = await api_client.post("/sessions")
    assert response.status_code == 201
    session_id = response.json()["id"]

    inbox = await api_client.get(
        "/inbox",
        headers={"X-Session-Id": session_id},
    )
    assert inbox.status_code == 200
    items = inbox.json()["items"]
    assert len(items) > 0
    assert all(item["status"] == EmailStatus.PENDING for item in items)


async def test_inbox_is_isolated_per_session(
    api_client, db_session, demo_session
) -> None:
    other = await demo_sessions_repo.create_empty_session(db_session)
    db_session.add(
        Email(
            session_id=other.id,
            sender="other@example.com",
            subject="Other session only",
            body="should not appear",
            received_at=datetime.now(UTC),
            status=EmailStatus.PENDING,
        )
    )
    await db_session.commit()

    response = await api_client.get("/inbox")
    assert response.status_code == 200
    subjects = {item["subject"] for item in response.json()["items"]}
    assert "Other session only" not in subjects
