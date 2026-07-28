from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from leaseops.models.schemas import EmailStatus


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


async def test_list_inbox(api_client) -> None:
    await api_client.post("/inbox", json=_email_payload())
    await api_client.post("/inbox", json=_email_payload(status=EmailStatus.PROCESSED))

    response = await api_client.get("/inbox")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

    filtered = await api_client.get("/inbox", params={"status": "processed"})
    assert filtered.status_code == 200
    items = filtered.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == EmailStatus.PROCESSED


async def test_get_email(api_client) -> None:
    create_response = await api_client.post("/inbox", json=_email_payload())
    email_id = create_response.json()["id"]

    response = await api_client.get(f"/inbox/{email_id}")
    assert response.status_code == 200
    assert response.json()["id"] == email_id


async def test_get_unknown_email_is_404(api_client) -> None:
    response = await api_client.get(f"/inbox/{uuid4()}")
    assert response.status_code == 404
