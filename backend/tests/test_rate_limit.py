from __future__ import annotations

from uuid import uuid4


async def test_start_run_returns_429_after_limit(api_client) -> None:
    payload = {"email_id": str(uuid4())}

    for _ in range(10):
        response = await api_client.post("/runs", json=payload)
        assert response.status_code == 404

    response = await api_client.post("/runs", json=payload)
    assert response.status_code == 429


async def test_stream_run_returns_429_after_limit(api_client) -> None:
    payload = {"email_id": str(uuid4())}

    for _ in range(10):
        response = await api_client.post("/runs/stream", json=payload)
        assert response.status_code == 404

    response = await api_client.post("/runs/stream", json=payload)
    assert response.status_code == 429


async def test_rerun_stream_returns_429_after_limit(api_client) -> None:
    payload = {"email_id": str(uuid4())}

    for _ in range(10):
        response = await api_client.post("/runs/rerun/stream", json=payload)
        assert response.status_code == 404

    response = await api_client.post("/runs/rerun/stream", json=payload)
    assert response.status_code == 429
