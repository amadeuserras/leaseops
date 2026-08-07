from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import (  # pyright: ignore[reportMissingTypeStubs]
    END,
    START,
    StateGraph,
)

from leaseops.agent.approval import approval
from leaseops.agent.classify import classify
from leaseops.agent.draft import draft
from leaseops.agent.enums import EmailCategory
from leaseops.agent.execute import execute
from leaseops.agent.extract import extract
from leaseops.agent.lease_check import lease_check
from leaseops.agent.plan import plan
from leaseops.agent.state import AgentState

_AfterClassify = Literal["extract", "end"]
_AfterExtract = Literal["lease_check", "draft"]
_AfterApproval = Literal["execute", "end"]


async def _classify_node(state: AgentState) -> dict[str, Any]:
    return (await classify(state)).model_dump()


async def _extract_node(state: AgentState) -> dict[str, Any]:
    return (await extract(state)).model_dump()


async def _lease_check_node(state: AgentState) -> dict[str, Any]:
    return (await lease_check(state)).model_dump()


async def _draft_node(state: AgentState) -> dict[str, Any]:
    return (await draft(state)).model_dump()


def _plan_node(state: AgentState) -> dict[str, Any]:
    return plan(state).model_dump()


def _approval_node(state: AgentState) -> dict[str, Any]:
    return approval(state).model_dump()


async def _execute_node(state: AgentState) -> dict[str, Any]:
    return (await execute(state)).model_dump()


def _after_classify(state: AgentState) -> _AfterClassify:
    if state.category == EmailCategory.NOT_OUR_PROBLEM:
        return "end"
    return "extract"


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
    graph.add_conditional_edges(
        "classify",
        _after_classify,
        {"extract": "extract", "end": END},
    )
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
