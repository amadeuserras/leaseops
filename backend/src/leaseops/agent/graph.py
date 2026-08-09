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


def _after_classify(state: AgentState) -> Literal["extract", "end"]:
    if state.category == EmailCategory.NOT_OUR_PROBLEM:
        return "end"
    return "extract"


def _after_extract(state: AgentState) -> Literal["lease_check", "draft"]:
    if state.category == EmailCategory.EMERGENCY:
        return "draft"
    return "lease_check"


def _after_approval(state: AgentState) -> Literal["execute", "end"]:
    if state.approved:
        return "execute"
    return "end"


def build_graph(checkpointer: Any = None) -> Any:
    graph: Any = StateGraph(AgentState)
    graph.add_node("classify", classify)
    graph.add_node("extract", extract)
    graph.add_node("lease_check", lease_check)
    graph.add_node("draft", draft)
    graph.add_node("plan", plan)
    graph.add_node("approval", approval)
    graph.add_node("execute", execute)

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
