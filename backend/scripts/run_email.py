from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from leaseops.agent.approval import ApprovalDecision, ApprovalRequest
from leaseops.agent.checkpoint import CHECKPOINT_SERDE
from leaseops.agent.graph import build_graph
from leaseops.agent.state import AgentState
from leaseops.db import emails as repo
from leaseops.db.models import Email
from leaseops.db.session import SessionLocal


def _print_delta(node: str, delta: dict[str, Any]) -> None:
    print(f"\n=== {node} ===")
    print(json.dumps(delta, indent=2, default=str))


def _prompt_for_decision(request: ApprovalRequest) -> ApprovalDecision:
    print("\n=== approval required ===")
    print(f"Action:  {request['action_type']}")
    print(f"Why:     {request['summary']}")
    print(f"Tenant:  {request['tenant_name']} (unit {request['unit']})")
    print(f"Issue:   {request['issue_summary']}")
    print(f"\nDraft reply:\n{request['draft']}\n")

    if input("Approve this action? [y/N] ").strip().lower() in {"y", "yes"}:
        return {"approved": True}
    reason = input("Rejection reason (optional): ").strip()
    return {"approved": False, "rejection_reason": reason or None}


async def _stream(graph: Any, inputs: Any, config: dict[str, Any]) -> None:
    async for item in graph.astream(inputs, config, stream_mode="updates"):
        updates = cast(dict[str, Any], item)
        for node, delta in updates.items():
            if node.startswith("__"):
                continue
            _print_delta(node, cast(dict[str, Any], delta))


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

    graph = build_graph(InMemorySaver(serde=CHECKPOINT_SERDE))
    config: dict[str, Any] = {"configurable": {"thread_id": str(email.id)}}
    inputs: Any = initial
    while True:
        await _stream(graph, inputs, config)
        snapshot = await graph.aget_state(config)
        if not snapshot.interrupts:
            return
        request = cast(ApprovalRequest, snapshot.interrupts[0].value)
        # basedpyright misses Command's dataclass-synthesized __init__.
        inputs = Command(resume=_prompt_for_decision(request))  # pyright: ignore[reportCallIssue]


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push one inbox email through the agent graph and print state.",
    )
    parser.add_argument(
        "subject",
        help="Exact email subject line (from the seeded inbox)",
    )
    args = parser.parse_args()

    async with SessionLocal() as session:
        email = await repo.get_email_by_subject(session, args.subject)
    if email is None:
        raise SystemExit(f"no inbox email found for subject: {args.subject}")
    await _run(email)


if __name__ == "__main__":
    asyncio.run(main())
