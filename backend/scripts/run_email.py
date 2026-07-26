from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, cast

from leaseops.agent.graph import build_graph
from leaseops.agent.state import AgentState
from leaseops.db import emails as repo
from leaseops.db.models import Email
from leaseops.db.session import SessionLocal


def _print_state(node: str, state: dict[str, Any]) -> None:
    print(f"\n=== {node} ===")
    dumped = AgentState.model_validate(state).model_dump(mode="json")
    print(json.dumps(dumped, indent=2))


async def _run(email: Email) -> None:
    initial = AgentState(
        email_id=email.id,
        sender=email.sender,
        subject=email.subject,
        body=email.body,
    )
    print(f"Running email {email.id}")
    print(f"From: {email.sender}")
    print(f"Subject: {email.subject}")

    graph = build_graph()
    pending_node: str | None = None
    async for item in graph.astream(initial, stream_mode=["updates", "values"]):
        mode, payload = cast(tuple[str, Any], item)
        if mode == "updates":
            pending_node = next(iter(cast(dict[str, Any], payload)))
        elif mode == "values" and pending_node is not None:
            _print_state(pending_node, cast(dict[str, Any], payload))
            pending_node = None


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push one inbox email through the agent graph and print state.",
    )
    parser.add_argument(
        "sender",
        help="Sender email address (uses their most recent inbox message)",
    )
    args = parser.parse_args()

    async with SessionLocal() as session:
        email = await repo.get_latest_email_by_sender(session, args.sender)
    if email is None:
        raise SystemExit(f"no inbox email found for sender: {args.sender}")
    await _run(email)


if __name__ == "__main__":
    asyncio.run(main())
