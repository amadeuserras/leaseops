from __future__ import annotations

import argparse
import asyncio
import json
from uuid import UUID

import httpx
from rich import print_json

from leaseops.core.config import settings
from leaseops.db import emails as repo
from leaseops.db.session import open_session, use_database

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_EMAIL = "Can we paint the living room?"
TIMEOUT = 300.0


async def _resolve_email_id(
    *, email_id: UUID | None, subject: str | None
) -> tuple[str, str | None]:
    if email_id is not None:
        return str(email_id), None
    if subject is None:
        raise SystemExit("pass either --email-id or --subject")

    async with open_session() as session:
        email = await repo.get_email_by_subject(session, subject)
    if email is None:
        raise SystemExit(f"no inbox email found for subject: {subject}")
    return str(email.id), email.subject


async def _stream_events(*, base_url: str, email_id: str) -> None:
    headers = {"Accept": "text/event-stream"}
    payload = {"email_id": email_id}

    async with (
        httpx.AsyncClient(base_url=base_url, timeout=TIMEOUT) as client,
        client.stream(
            "POST", "/runs/stream", json=payload, headers=headers
        ) as response,
    ):
        if response.status_code >= 400:
            body = (await response.aread()).decode()
            raise SystemExit(f"request failed ({response.status_code}): {body}")

        print(f"Streaming from {base_url}/runs/stream for email_id={email_id}")

        data_lines: list[str] = []
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").lstrip(" "))
                continue

            if line != "":
                continue

            if not data_lines:
                continue

            payload_text = "\n".join(data_lines)
            print_json(data=json.loads(payload_text), default=str)
            data_lines = []

        if data_lines:
            payload_text = "\n".join(data_lines)
            print_json(data=json.loads(payload_text), default=str)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description=("Call POST /runs/stream and print each SSE event in the terminal.")
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="API base URL for the FastAPI app",
    )
    parser.add_argument(
        "--email-id",
        type=UUID,
        help="Email UUID to stream",
    )
    parser.add_argument(
        "--subject",
        default=DEFAULT_EMAIL,
        help="Exact email subject to look up locally if --email-id is omitted",
    )
    args = parser.parse_args()

    async with use_database(settings.database_url):
        email_id, resolved_subject = await _resolve_email_id(
            email_id=args.email_id, subject=args.subject
        )
        if resolved_subject is not None:
            print(f"Resolved subject to email_id={email_id}: {resolved_subject}")

        await _stream_events(base_url=args.base_url, email_id=email_id)


if __name__ == "__main__":
    asyncio.run(main())
