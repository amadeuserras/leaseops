from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from leaseops.agent.checkpoint import CHECKPOINT_SERDE
from leaseops.agent.graph import _after_classify, _after_extract
from leaseops.agent.runner import GraphRunner
from leaseops.agent.state import AgentState, EmailCategory
from leaseops.agent.step_schemas import ClassifyOutput
from leaseops.db import emails as emails_repo
from leaseops.db import runs as runs_repo
from leaseops.db import steps as steps_repo
from leaseops.db.models import Email
from leaseops.models.enums import EmailStatus, RunStatus


def _base_state(**overrides: object) -> AgentState:
    data: dict[str, object] = {
        "email_id": uuid4(),
        "sender": "tenant@example.com",
        "subject": "test",
        "body": "body",
        "received_at": datetime.now(UTC),
    }
    data.update(overrides)
    return AgentState.model_validate(data)


def test_after_classify_not_our_problem_ends() -> None:
    state = _base_state(category=EmailCategory.NOT_OUR_PROBLEM)
    assert _after_classify(state) == "end"


def test_after_classify_other_categories_extract() -> None:
    for category in (
        EmailCategory.MAINTENANCE,
        EmailCategory.LEASE_QUESTION,
        EmailCategory.EMERGENCY,
    ):
        assert _after_classify(_base_state(category=category)) == "extract"


def test_after_extract_emergency_skips_lease_check() -> None:
    state = _base_state(category=EmailCategory.EMERGENCY)
    assert _after_extract(state) == "draft"


def test_after_extract_maintenance_goes_to_lease_check() -> None:
    state = _base_state(category=EmailCategory.MAINTENANCE)
    assert _after_extract(state) == "lease_check"


def _classify_not_our_problem(state: AgentState) -> dict[str, Any]:
    _ = state
    return ClassifyOutput(category=EmailCategory.NOT_OUR_PROBLEM).model_dump()


def _extract_should_not_run(state: AgentState) -> dict[str, Any]:
    raise AssertionError(f"extract must not run for not_our_problem: {state.category}")


def build_not_our_problem_graph(checkpointer: Any) -> Any:
    graph: Any = StateGraph(AgentState)
    graph.add_node("classify", _classify_not_our_problem)
    graph.add_node("extract", _extract_should_not_run)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        _after_classify,
        {"extract": "extract", "end": END},
    )
    return graph.compile(checkpointer=checkpointer)


@pytest.fixture
def not_our_problem_runner() -> GraphRunner:
    return GraphRunner(
        graph=build_not_our_problem_graph(InMemorySaver(serde=CHECKPOINT_SERDE))
    )


async def test_not_our_problem_stream_ends_processed(
    db_session, not_our_problem_runner: GraphRunner
) -> None:
    email = Email(
        sender="spam@example.com",
        subject=f"Buy crypto {uuid4()}",
        body="Totally unrelated sales pitch.",
        received_at=datetime.now(UTC),
        status=EmailStatus.PENDING,
    )
    db_session.add(email)
    await db_session.commit()
    await db_session.refresh(email)

    events = [
        event async for event in not_our_problem_runner.stream(db_session, email)
    ]

    assert events[-1]["type"] == "run_finished"
    assert events[-1]["status"] == RunStatus.DONE.value

    email = await emails_repo.get_email_by_id(db_session, email.id)
    assert email is not None
    assert email.status == EmailStatus.PROCESSED

    run = await runs_repo.get_run_by_email_id(db_session, email.id)
    assert run is not None
    assert run.status == RunStatus.DONE

    steps = await steps_repo.list_steps_for_run(db_session, run.id)
    assert [step.node_name for step in steps] == ["classify"]
