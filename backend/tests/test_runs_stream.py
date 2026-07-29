from __future__ import annotations

from uuid import uuid4


async def test_stream_run_unknown_email_is_404(api_client) -> None:
    response = await api_client.post("/runs/stream", json={"email_id": str(uuid4())})
    assert response.status_code == 404
