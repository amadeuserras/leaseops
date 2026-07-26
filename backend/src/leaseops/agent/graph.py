from __future__ import annotations

from dataclasses import asdict
from typing import Any, Literal

from langgraph.graph import (  # pyright: ignore[reportMissingTypeStubs]
    END,
    START,
    StateGraph,
)

from leaseops.agent.classify import classify
from leaseops.agent.decide import decide
from leaseops.agent.draft import draft
from leaseops.agent.extract import extract
from leaseops.agent.lease_check import lease_check
from leaseops.agent.state import ActionType, AgentState, EmailCategory, Status

_Route = Literal["extract", "escalate"]


async def _classify_node(state: AgentState) -> dict[str, Any]:
    return asdict(await classify(state))


async def _extract_node(state: AgentState) -> dict[str, Any]:
    return asdict(await extract(state))


async def _lease_check_node(state: AgentState) -> dict[str, Any]:
    return asdict(await lease_check(state))


def _decide_node(state: AgentState) -> dict[str, Any]:
    return asdict(decide(state))


async def _draft_node(state: AgentState) -> dict[str, Any]:
    return asdict(await draft(state))


def _escalate_node(state: AgentState) -> dict[str, Any]:
    _ = state
    return {
        "action_type": ActionType.ESCALATE,
        "summary": "Emergency safety risk — escalate to a human immediately.",
        "status": Status.ESCALATED,
    }


def _after_classify(state: AgentState) -> _Route:
    if state.category == EmailCategory.EMERGENCY:
        return "escalate"
    return "extract"


def build_graph() -> Any:
    graph: Any = StateGraph(AgentState)
    graph.add_node("classify", _classify_node)
    graph.add_node("extract", _extract_node)
    graph.add_node("lease_check", _lease_check_node)
    graph.add_node("decide", _decide_node)
    graph.add_node("draft", _draft_node)
    graph.add_node("escalate", _escalate_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        _after_classify,
        {"extract": "extract", "escalate": "escalate"},
    )
    graph.add_edge("extract", "lease_check")
    graph.add_edge("lease_check", "decide")
    graph.add_edge("decide", "draft")
    graph.add_edge("draft", END)
    graph.add_edge("escalate", END)
    return graph.compile()
