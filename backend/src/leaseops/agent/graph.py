from __future__ import annotations

from dataclasses import asdict
from typing import Any, Literal

from langgraph.graph import (  # pyright: ignore[reportMissingTypeStubs]
    END,
    START,
    StateGraph,
)

from leaseops.agent.approval import approval
from leaseops.agent.classify import classify
from leaseops.agent.draft import draft
from leaseops.agent.execute import execute
from leaseops.agent.extract import extract
from leaseops.agent.lease_check import lease_check
from leaseops.agent.plan import plan
from leaseops.agent.state import AgentState, EmailCategory

_AfterExtract = Literal["lease_check", "draft"]
_AfterApproval = Literal["execute", "end"]


async def _classify_node(state: AgentState) -> dict[str, Any]:
    return asdict(await classify(state))


async def _extract_node(state: AgentState) -> dict[str, Any]:
    return asdict(await extract(state))


async def _lease_check_node(state: AgentState) -> dict[str, Any]:
    return asdict(await lease_check(state))


async def _draft_node(state: AgentState) -> dict[str, Any]:
    return asdict(await draft(state))


def _plan_node(state: AgentState) -> dict[str, Any]:
    return asdict(plan(state))


def _approval_node(state: AgentState) -> dict[str, Any]:
    return asdict(approval(state))


async def _execute_node(state: AgentState) -> dict[str, Any]:
    return asdict(await execute(state))


def _after_extract(state: AgentState) -> _AfterExtract:
    if state.category == EmailCategory.EMERGENCY:
        return "draft"
    return "lease_check"


def _after_approval(state: AgentState) -> _AfterApproval:
    if state.approved:
        return "execute"
    return "end"


def build_graph(checkpointer: Any = None) -> Any:
    graph: Any = StateGraph(AgentState)
    graph.add_node("classify", _classify_node)
    graph.add_node("extract", _extract_node)
    graph.add_node("lease_check", _lease_check_node)
    graph.add_node("draft", _draft_node)
    graph.add_node("plan", _plan_node)
    graph.add_node("approval", _approval_node)
    graph.add_node("execute", _execute_node)

    graph.add_edge(START, "classify")
    graph.add_edge("classify", "extract")
    graph.add_conditional_edges(
        "extract",
        _after_extract,
        {"lease_check": "lease_check", "draft": "draft"},
    )
    graph.add_edge("lease_check", "draft")
    graph.add_edge("draft", "plan")
    graph.add_edge("plan", "approval")
    graph.add_conditional_edges(
        "approval",
        _after_approval,
        {"execute": "execute", "end": END},
    )
    graph.add_edge("execute", END)
    return graph.compile(checkpointer=checkpointer)
