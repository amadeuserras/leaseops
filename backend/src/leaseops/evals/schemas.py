from __future__ import annotations

from leaseops.agent.state import PlanAction, QAResultSchema
from leaseops.core.base import LeaseOpsModel


class GoldenEmail(LeaseOpsModel):
    sender: str
    subject: str
    body: str


class GoldenLeaseCheck(LeaseOpsModel):
    responsibility: str


class GoldenWrites(LeaseOpsModel):
    before_approval: list[PlanAction]
    after_approval: list[PlanAction]


class GoldenItem(LeaseOpsModel):
    id: str
    email: GoldenEmail
    category: str
    lease_check: GoldenLeaseCheck | None = None
    writes: GoldenWrites | None = None


class CaseResult(LeaseOpsModel):
    id: str
    email: GoldenEmail
    returned_category: str | None
    returned_responsibility: str | None
    returned_lease_addresses_issue: bool | None
    returned_before_approval: list[PlanAction]
    returned_after_approval: list[PlanAction]
    returned_qa_results: list[QAResultSchema]
    golden_category: str
    golden_responsibility: str | None
    golden_before_approval: list[PlanAction]
    golden_after_approval: list[PlanAction]
    premature_write: bool
    post_approval_deviation: bool
    unauthorized_action: bool
    classification_match: bool
    missed_real_issue: bool | None
    missed_emergency: bool | None
    responsibility_match: bool | None
    landlord_issue_blamed_on_tenant: bool | None
    qa_calls: int | None
    cost_usd: float
    latency_s: float


class GlobalMetrics(LeaseOpsModel):
    unauthorized_rate: float
    unauthorized_n: int
    classification_acc: float
    classification_n: int
    missed_issue_rate: float
    missed_issue_n: int
    missed_emerg_rate: float
    missed_emerg_n: int
    resp_acc: float
    resp_n: int
    landlord_rate: float
    landlord_n: int
    mean_qa: float
    qa_n: int
    p95_cost: float
    p95_latency: float
    total_n: int
