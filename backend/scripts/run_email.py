from __future__ import annotations

import argparse
import asyncio
from typing import Any, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from leaseops.agent.checkpoint import CHECKPOINT_SERDE
from leaseops.agent.graph import build_graph
from leaseops.agent.state import AgentState
from leaseops.db import emails as repo
from leaseops.db.models import Email
from leaseops.db.session import SessionLocal

_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"

_LLM_NODES = frozenset({"classify", "extract", "lease_check", "draft"})
DEFAULT_EMAIL = "Can we paint the living room?"


def _node_title(node: str) -> str:
    if node in _LLM_NODES:
        return f"{node} (LLM)"
    return node


def _qa_pair(item: Any) -> tuple[str, str] | None:
    if isinstance(item, dict):
        question, answer = item.get("question"), item.get("answer")
    else:
        question, answer = (
            getattr(item, "question", None),
            getattr(item, "answer", None),
        )
    if question is None or answer is None:
        return None
    return str(question), str(answer)


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        if not value:
            return "[]"
        pairs = [_qa_pair(item) for item in value]
        if all(pair is not None for pair in pairs):
            blocks: list[str] = []
            for pair in pairs:
                assert pair is not None
                question, answer = pair
                blocks.append(
                    f"{_DIM}[Q]{_RESET} {question}\n{_DIM}[A]{_RESET} {answer}"
                )
            return "\n\n".join(blocks)
        return "\n".join(f"  - {_format_value(item)}" for item in value)
    if isinstance(value, dict):
        if not value:
            return "{}"
        return "\n".join(f"  {k}: {_format_value(v)}" for k, v in value.items())
    return str(value)


def _print_fields(delta: dict[str, Any]) -> None:
    if not delta:
        return
    width = max(len(key) for key in delta)
    for key, value in delta.items():
        formatted = _format_value(value)
        label = f"{_DIM}{key:<{width}}{_RESET}"
        if "\n" in formatted:
            indented = formatted.replace("\n", "\n" + " " * (width + 4))
            print(f"  {label}  {indented}")
        else:
            print(f"  {label}  {formatted}")


def _print_delta(node: str, delta: dict[str, Any], *, header: bool = True) -> None:
    if header:
        print(f"\n{_BOLD}── {_node_title(node)} ──{_RESET}")
    elif delta:
        print()
    _print_fields(delta)


def _prompt_for_decision(request: dict[str, Any]) -> dict[str, Any]:
    fields = ", ".join(request)
    print(f"\n{_BOLD}── {_node_title('approval_gate')} ──{_RESET}")
    print(f"  {_DIM}Fields shown to the human:{_RESET} {fields}")
    if input("\nApprove this action? [y/N] ").strip().lower() in {"y", "yes"}:
        return {"approved": True}
    reason = input("Rejection reason (optional): ").strip()
    return {"approved": False, "rejection_reason": reason or None}


async def _stream(
    graph: Any,
    inputs: Any,
    config: dict[str, Any],
    *,
    skip_headers: frozenset[str] = frozenset(),
) -> None:
    async for item in graph.astream(inputs, config, stream_mode="updates"):
        updates = cast(dict[str, Any], item)
        for node, delta in updates.items():
            if node.startswith("__"):
                continue
            _print_delta(
                node,
                cast(dict[str, Any], delta),
                header=node not in skip_headers,
            )


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
    skip_headers: frozenset[str] = frozenset()
    while True:
        await _stream(graph, inputs, config, skip_headers=skip_headers)
        snapshot = await graph.aget_state(config)
        if not snapshot.interrupts:
            return
        request = cast(dict[str, Any], snapshot.interrupts[0].value)
        # basedpyright misses Command's dataclass-synthesized __init__.
        inputs = Command(resume=_prompt_for_decision(request))  # pyright: ignore[reportCallIssue]
        skip_headers = frozenset({"approval_gate"})


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push one inbox email through the agent graph and print state.",
    )
    parser.add_argument(
        "subject",
        nargs="?",
        default=DEFAULT_EMAIL,
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
