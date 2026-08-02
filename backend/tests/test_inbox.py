from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from leaseops.models.enums import EmailStatus


def _email_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "sender": "tenant@example.com",
        "subject": f"Leaky faucet {uuid4()}",
        "body": "Kitchen sink is dripping.",
        "received_at": datetime.now(UTC).isoformat(),
    }
    payload.update(overrides)
    return payload


async def test_create_email(api_client) -> None:
    response = await api_client.post("/inbox", json=_email_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["sender"] == "tenant@example.com"
    assert body["status"] == EmailStatus.PENDING
    assert body["unit"] is None
    assert body["severity"] is None
    assert body["actions_taken"] == []


async def test_list_inbox(api_client) -> None:
    await api_client.post("/inbox", json=_email_payload())
    await api_client.post("/inbox", json=_email_payload(status=EmailStatus.PROCESSED))

    response = await api_client.get("/inbox")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["agent_last_ran_at"] is None

    filtered = await api_client.get("/inbox", params={"status": "processed"})
    assert filtered.status_code == 200
    items = filtered.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == EmailStatus.PROCESSED


async def test_list_inbox_includes_enrichment_fields(api_client, db_session) -> None:
    from leaseops.db.models import Run, Step, Tenant
    from leaseops.models.enums import RunStatus

    tenant = Tenant(
        email="tenant@example.com",
        name="Ada Tenant",
        document_id=uuid4(),
        address="1 Main St",
        unit="4B",
    )
    db_session.add(tenant)
    await db_session.commit()

    create_response = await api_client.post(
        "/inbox",
        json=_email_payload(status=EmailStatus.PROCESSED),
    )
    email_id = create_response.json()["id"]

    ended_at = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    run = Run(
        email_id=email_id,
        status=RunStatus.DONE,
        ended_at=ended_at,
    )
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    db_session.add_all(
        [
            Step(
                run_id=run.id,
                node_name="extract",
                output={"severity": "high"},
            ),
            Step(
                run_id=run.id,
                node_name="execute",
                output={"actions_taken": ["create_work_order", "send_reply"]},
            ),
        ]
    )
    await db_session.commit()

    response = await api_client.get("/inbox")
    assert response.status_code == 200
    body = response.json()
    item = next(i for i in body["items"] if i["id"] == email_id)
    assert item["unit"] == "4B"
    assert item["severity"] == "high"
    assert item["actions_taken"] == ["create_work_order", "send_reply"]
    assert body["agent_last_ran_at"] == ended_at.isoformat().replace("+00:00", "Z")


async def test_get_email(api_client) -> None:
    create_response = await api_client.post("/inbox", json=_email_payload())
    email_id = create_response.json()["id"]

    response = await api_client.get(f"/inbox/{email_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == email_id
    assert body["sender"] == "tenant@example.com"
    assert body["subject"]
    assert body["body"]
    assert body["received_at"]


async def test_get_unknown_email_is_404(api_client) -> None:
    response = await api_client.get(f"/inbox/{uuid4()}")
    assert response.status_code == 404
