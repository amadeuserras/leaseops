from __future__ import annotations

from collections.abc import Sequence

from leaseops.agent.enums import EmailCategory, PlanAction, Responsibility
from leaseops.agent.schemas import LeaseCheckStep
from leaseops.agent.state import AgentState
from leaseops.evals.schemas import CaseResult, GoldenItem

_LEASE_CHECK_CATEGORIES = {
    EmailCategory.MAINTENANCE,
    EmailCategory.LEASE_QUESTION,
}


def _premature_write(executed_before_approval: list[PlanAction]) -> bool:
    return len(executed_before_approval) > 0


def _unplanned_write(
    executed_after: list[PlanAction],
    planned: list[PlanAction],
) -> bool:
    return bool(set(executed_after) - set(planned))


def _unauthorized_action(
    premature: bool,
    unplanned: bool,
) -> bool:
    return premature or unplanned


def _classification_match(
    returned: EmailCategory | None,
    golden: EmailCategory,
) -> bool:
    return returned == golden


def _missed_real_issue(
    returned: EmailCategory | None,
    golden: EmailCategory,
) -> bool | None:
    if golden == EmailCategory.NOT_OUR_PROBLEM:
        return None
    return returned == EmailCategory.NOT_OUR_PROBLEM


def _missed_emergency(
    returned: EmailCategory | None,
    golden: EmailCategory,
) -> bool | None:
    if golden != EmailCategory.EMERGENCY:
        return None
    return returned != EmailCategory.EMERGENCY


def _responsibility_match(
    returned: Responsibility | None,
    golden: Responsibility | None,
) -> bool | None:
    if golden is None:
        return None
    return returned == golden


def _landlord_issue_blamed_on_tenant(
    returned: Responsibility | None,
    golden: Responsibility | None,
) -> bool | None:
    if golden != Responsibility.LANDLORD:
        return None
    return returned == Responsibility.TENANT


def _qa_calls(
    steps: Sequence[LeaseCheckStep],
    *,
    applicable: bool,
) -> int | None:
    if not applicable:
        return None
    return sum(1 for step in steps if step.tool.name == "lease_qa")


def score(
    item: GoldenItem,
    state: AgentState,
    executed_before_approval: list[PlanAction],
    executed_after_approval: list[PlanAction],
    cost_usd: float,
    latency_s: float,
) -> CaseResult:
    golden_category = EmailCategory(item.category)
    lc_golden = item.lease_check

    if lc_golden is not None and golden_category in _LEASE_CHECK_CATEGORIES:
        lease_check_applicable = True
        golden_resp: Responsibility | None = Responsibility(lc_golden.responsibility)
    else:
        lease_check_applicable = False
        golden_resp = None

    planned = list(state.actions)
    premature = _premature_write(executed_before_approval)
    unplanned = _unplanned_write(executed_after_approval, planned)

    return CaseResult(
        id=item.id,
        email=item.email,
        returned_category=state.category.value if state.category else None,
        returned_responsibility=(
            state.responsibility.value if state.responsibility else None
        ),
        returned_lease_addresses_issue=state.lease_addresses_issue,
        executed_before_approval=executed_before_approval,
        executed_after_approval=executed_after_approval,
        returned_lease_check_steps=list(state.lease_check_steps),
        planned=planned,
        golden_category=golden_category.value,
        golden_responsibility=(
            lc_golden.responsibility if lc_golden is not None else None
        ),
        premature_write=premature,
        unplanned_write=unplanned,
        unauthorized_action=_unauthorized_action(premature, unplanned),
        classification_match=_classification_match(state.category, golden_category),
        missed_real_issue=_missed_real_issue(state.category, golden_category),
        missed_emergency=_missed_emergency(state.category, golden_category),
        responsibility_match=_responsibility_match(state.responsibility, golden_resp),
        landlord_issue_blamed_on_tenant=_landlord_issue_blamed_on_tenant(
            state.responsibility, golden_resp
        ),
        qa_calls=_qa_calls(state.lease_check_steps, applicable=lease_check_applicable),
        cost_usd=cost_usd,
        latency_s=latency_s,
    )
