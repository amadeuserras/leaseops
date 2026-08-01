from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from leaseops.agent.approval import approval
from leaseops.agent.checkpoint import CHECKPOINT_SERDE
from leaseops.agent.runner import GraphRunner
from leaseops.agent.state import (
    AgentState,
    EmailCategory,
    PlanAction,
    QAResultSchema,
    Responsibility,
    Severity,
)
from leaseops.db.models import Email
from leaseops.models.enums import EmailStatus, RunStatus


def _after_approval(state: AgentState) -> str:
    if state.approved:
        return "execute"
    return "end"


def _seed_node(state: AgentState) -> dict[str, Any]:
    _ = state
    return {
        "category": EmailCategory.MAINTENANCE,
        "severity": Severity.MEDIUM,
        "actions": [PlanAction.CREATE_WORK_ORDER, PlanAction.SEND_REPLY],
        "draft": "We'll send someone out tomorrow.",
        "tenant_name": "Ada Tenant",
        "unit": "2A",
        "address": "12 Example Street",
        "issue_summary": "leaky faucet",
        "appliance_or_system": "faucet",
        "responsibility": Responsibility.LANDLORD,
        "qa_results": [
            QAResultSchema(
                question="Who is responsible for faucet repairs?",
                answer="Landlord. [hardcoded-lease §7.2]",
                citations=["[hardcoded-lease §7.2]"],
            )
        ],
    }


def _approval_node(state: AgentState) -> dict[str, Any]:
    return asdict(approval(state))


def _execute_node(state: AgentState) -> dict[str, Any]:
    _ = state
    return {}


def build_test_graph(checkpointer: Any) -> Any:
    graph: Any = StateGraph(AgentState)
    graph.add_node("seed", _seed_node)
    graph.add_node("approval", _approval_node)
    graph.add_node("execute", _execute_node)
    graph.add_edge(START, "seed")
    graph.add_edge("seed", "approval")
    graph.add_conditional_edges(
        "approval",
        _after_approval,
        {"execute": "execute", "end": END},
    )
    graph.add_edge("execute", END)
    return graph.compile(checkpointer=checkpointer)


@pytest.fixture
def runner() -> GraphRunner:
    return GraphRunner(graph=build_test_graph(InMemorySaver(serde=CHECKPOINT_SERDE)))


async def _seed_email(db_session) -> Email:
    email = Email(
        sender="tenant@example.com",
        subject=f"Approval test {uuid4()}",
        body="Kitchen sink is dripping.",
        received_at=datetime.now(UTC),
        status=EmailStatus.PENDING,
    )
    db_session.add(email)
    await db_session.commit()
    await db_session.refresh(email)
    return email


async def test_list_approve_flow(api_client, db_session) -> None:
    email = await _seed_email(db_session)

    run_response = await api_client.post("/runs", json={"email_id": str(email.id)})
    assert run_response.status_code == 201
    run = run_response.json()
    assert run["status"] == RunStatus.PAUSED

    approvals_response = await api_client.get("/approvals")
    assert approvals_response.status_code == 200
    items = approvals_response.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["run_id"] == run["id"]
    assert item["email_id"] == str(email.id)
    assert item["category"] == EmailCategory.MAINTENANCE
    assert item["severity"] == Severity.MEDIUM
    assert item["tenant_name"] == "Ada Tenant"
    assert item["unit"] == "2A"
    assert item["address"] == "12 Example Street"
    assert item["issue_summary"] == "leaky faucet"
    assert item["appliance_or_system"] == "faucet"
    assert item["responsibility"] == Responsibility.LANDLORD
    assert item["citation"] == "[hardcoded-lease §7.2]"
    assert item["original_email"] == "Kitchen sink is dripping."
    assert item["draft"] == "We'll send someone out tomorrow."
    assert item["actions"] == [
        PlanAction.CREATE_WORK_ORDER,
        PlanAction.SEND_REPLY,
    ]

    approve_response = await api_client.post(f"/approvals/{run['id']}/approve")
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == RunStatus.DONE

    approvals_response = await api_client.get("/approvals")
    assert approvals_response.json()["items"] == []


async def test_reject_completes(api_client, db_session) -> None:
    email = await _seed_email(db_session)

    run_response = await api_client.post("/runs", json={"email_id": str(email.id)})
    run_id = run_response.json()["id"]

    reject_response = await api_client.post(f"/approvals/{run_id}/reject")

    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == RunStatus.DONE


async def test_approve_unknown_run_is_404(api_client) -> None:
    approve_response = await api_client.post(f"/approvals/{uuid4()}/approve")
    assert approve_response.status_code == 404


async def test_approve_when_not_paused_is_409(api_client, db_session) -> None:
    email = await _seed_email(db_session)

    run_response = await api_client.post("/runs", json={"email_id": str(email.id)})
    run_id = run_response.json()["id"]
    await api_client.post(f"/approvals/{run_id}/approve")

    approve_response = await api_client.post(f"/approvals/{run_id}/approve")
    assert approve_response.status_code == 409
