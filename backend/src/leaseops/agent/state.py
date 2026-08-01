from __future__ import annotations

from uuid import UUID

from leaseops.agent.types import (
    EmailCategory,
    PlanAction,
    QAResultSchema,
    Responsibility,
    Severity,
)
from leaseops.models.schemas import LeaseOpsModel


class AgentState(LeaseOpsModel):
    # ingest
    email_id: UUID
    sender: str
    subject: str
    body: str

    # classify
    category: EmailCategory | None = None

    # extract
    tenant_name: str | None = None
    unit: str | None = None
    address: str | None = None
    issue_summary: str | None = None
    severity: Severity | None = None
    appliance_or_system: str | None = None

    # lease_check
    responsibility: Responsibility | None = None
    lease_addresses_issue: bool | None = None
    qa_results: list[QAResultSchema] = []

    # draft
    draft: str | None = None

    # plan
    actions: list[PlanAction] = []

    # approval
    approved: bool | None = None
    rejection_reason: str | None = None
