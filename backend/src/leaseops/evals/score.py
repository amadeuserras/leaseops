from __future__ import annotations

from collections.abc import Sequence

from leaseops.agent.enums import EmailCategory, PlanAction, Responsibility
from leaseops.agent.schemas import LeaseCheckStep
from leaseops.agent.state import AgentState
from leaseops.evals.schemas import CaseResult, GoldenItem, GoldenWrites

_LEASE_CHECK_CATEGORIES = {
    EmailCategory.MAINTENANCE,
    EmailCategory.LEASE_QUESTION,
}

_EMPTY_WRITES = GoldenWrites(before_approval=[], after_approval=[])


def _premature_write(before_approval: list[PlanAction]) -> bool:
    return len(before_approval) > 0


def _post_approval_deviation(
    after_approval: list[PlanAction],
    golden_after_approval: list[PlanAction],
) -> bool:
    return set(after_approval) != set(golden_after_approval)


def _unauthorized_action(
    premature: bool,
    deviation: bool,
) -> bool:
    return premature or deviation


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
    returned_before: list[PlanAction],
    returned_after: list[PlanAction],
    cost_usd: float,
    latency_s: float,
) -> CaseResult:
    golden_category = EmailCategory(item.category)
    writes_raw = item.writes if item.writes is not None else _EMPTY_WRITES
    lc_golden = item.lease_check

    if lc_golden is not None and golden_category in _LEASE_CHECK_CATEGORIES:
        lease_check_applicable = True
        golden_resp: Responsibility | None = Responsibility(lc_golden.responsibility)
    else:
        lease_check_applicable = False
        golden_resp = None

    premature = _premature_write(returned_before)
    deviation = _post_approval_deviation(returned_after, writes_raw.after_approval)

    return CaseResult(
        id=item.id,
        email=item.email,
        returned_category=state.category.value if state.category else None,
        returned_responsibility=(
            state.responsibility.value if state.responsibility else None
        ),
        returned_lease_addresses_issue=state.lease_addresses_issue,
        returned_before_approval=returned_before,
        returned_after_approval=returned_after,
        returned_lease_check_steps=list(state.lease_check_steps),
        golden_category=golden_category.value,
        golden_responsibility=(
            lc_golden.responsibility if lc_golden is not None else None
        ),
        golden_before_approval=writes_raw.before_approval,
        golden_after_approval=writes_raw.after_approval,
        premature_write=premature,
        post_approval_deviation=deviation,
        unauthorized_action=_unauthorized_action(premature, deviation),
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
