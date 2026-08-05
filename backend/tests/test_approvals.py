from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from leaseops.agent.approval import approval
from leaseops.agent.checkpoint import CHECKPOINT_SERDE
from leaseops.agent.runner import GraphRunner
from leaseops.agent.schemas import (
    ClassifyOutput,
    DraftOutput,
    ExecuteOutput,
    ExtractOutput,
    LeaseCheckOutput,
    PlanOutput,
)
from leaseops.agent.state import (
    AgentState,
    EmailCategory,
    PlanAction,
    QAResultSchema,
    Responsibility,
    Severity,
)
from leaseops.db import emails as emails_repo
from leaseops.db import runs as runs_repo
from leaseops.db import steps as steps_repo
from leaseops.db.models import Email
from leaseops.models.enums import EmailStatus, RunStatus


def _after_approval(state: AgentState) -> str:
    if state.approved:
        return "execute"
    return "end"


def _classify_node(state: AgentState) -> dict[str, Any]:
    _ = state
    return ClassifyOutput(category=EmailCategory.MAINTENANCE).model_dump()


def _extract_node(state: AgentState) -> dict[str, Any]:
    _ = state
    return ExtractOutput(
        tenant_name="Ada Tenant",
        unit="2A",
        address="12 Example Street",
        document_id=None,
        issue_summary="leaky faucet",
        severity=Severity.MEDIUM,
        appliance_or_system="faucet",
    ).model_dump()


def _lease_check_node(state: AgentState) -> dict[str, Any]:
    _ = state
    return LeaseCheckOutput(
        lease_addresses_issue=True,
        responsibility=Responsibility.LANDLORD,
        qa_results=[
            QAResultSchema(
                question="Who is responsible for faucet repairs?",
                answer="Landlord. [hardcoded-lease §7.2]",
                citations=["[hardcoded-lease §7.2]"],
                reasoning="Checking lease responsibility for faucet repairs.",
            )
        ],
    ).model_dump()


def _draft_node(state: AgentState) -> dict[str, Any]:
    _ = state
    return DraftOutput(draft="We'll send someone out tomorrow.").model_dump()


def _plan_node(state: AgentState) -> dict[str, Any]:
    _ = state
    return PlanOutput(
        actions=[PlanAction.CREATE_WORK_ORDER, PlanAction.SEND_REPLY]
    ).model_dump()


def _approval_node(state: AgentState) -> dict[str, Any]:
    return approval(state).model_dump()


def _execute_node(state: AgentState) -> dict[str, Any]:
    _ = state
    return ExecuteOutput(succeeded=True).model_dump()


def build_test_graph(checkpointer: Any) -> Any:
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
    graph.add_edge("extract", "lease_check")
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

    await db_session.refresh(email)
    assert email.status == EmailStatus.AWAITING_APPROVAL

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

    await db_session.refresh(email)
    assert email.status == EmailStatus.PROCESSED

    steps = await steps_repo.list_steps_for_run(db_session, UUID(run["id"]))
    execute_steps = [step for step in steps if step.node_name == "execute"]
    assert len(execute_steps) == 1
    assert execute_steps[0].output == {"succeeded": True}

    approvals_response = await api_client.get("/approvals")
    assert approvals_response.json()["items"] == []


async def test_reject_completes(api_client, db_session) -> None:
    email = await _seed_email(db_session)

    run_response = await api_client.post("/runs", json={"email_id": str(email.id)})
    run_id = run_response.json()["id"]

    await db_session.refresh(email)
    assert email.status == EmailStatus.AWAITING_APPROVAL

    reject_response = await api_client.post(f"/approvals/{run_id}/reject")

    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == RunStatus.DONE

    await db_session.refresh(email)
    assert email.status == EmailStatus.PROCESSED


async def test_stream_persists_approval_step(db_session, runner) -> None:
    email = await _seed_email(db_session)
    events = [event async for event in runner.stream(db_session, email)]

    assert any(event.get("type") == "paused" for event in events)
    assert events[-1] == {"type": "run_finished", "status": RunStatus.PAUSED}

    run = await runs_repo.get_run_by_email_id(db_session, email.id)
    assert run is not None
    assert run.status == RunStatus.PAUSED

    steps = await steps_repo.list_steps_for_run(db_session, run.id)
    assert [step.node_name for step in steps] == [
        "classify",
        "extract",
        "lease_check",
        "draft",
        "plan",
        "approval",
    ]
    assert steps[-1].output is not None
    assert steps[-1].output["draft"] == "We'll send someone out tomorrow."


async def test_approve_after_stream_persists_execute(db_session, runner) -> None:
    email = await _seed_email(db_session)
    async for _ in runner.stream(db_session, email):
        pass

    run = await runs_repo.get_run_by_email_id(db_session, email.id)
    assert run is not None

    await runner.approve(db_session, run.id)

    steps = await steps_repo.list_steps_for_run(db_session, run.id)
    assert [step.node_name for step in steps] == [
        "classify",
        "extract",
        "lease_check",
        "draft",
        "plan",
        "approval",
        "execute",
    ]
    assert steps[-1].output == {"succeeded": True}


async def test_stream_rerun_wipes_and_creates_new_run(db_session, runner) -> None:
    email = await _seed_email(db_session)

    async for _ in runner.stream(db_session, email):
        pass
    first = await runs_repo.get_run_by_email_id(db_session, email.id)
    assert first is not None
    first_id = first.id
    first_steps = await steps_repo.list_steps_for_run(db_session, first_id)
    assert len(first_steps) == 6

    await runner.wipe(db_session, email.id)
    assert await runs_repo.get_run(db_session, first_id) is None

    email = await emails_repo.get_email_by_id(db_session, email.id)
    assert email is not None
    assert email.status == EmailStatus.PENDING

    async for _ in runner.stream(db_session, email):
        pass
    second = await runs_repo.get_run_by_email_id(db_session, email.id)
    assert second is not None
    assert second.id != first_id

    steps = await steps_repo.list_steps_for_run(db_session, second.id)
    assert [step.node_name for step in steps] == [
        "classify",
        "extract",
        "lease_check",
        "draft",
        "plan",
        "approval",
    ]


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
