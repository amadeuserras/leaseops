from __future__ import annotations

from uuid import UUID

from leaseops.agent.types import (
    ActionType,
    EmailCategory,
    IssueCategory,
    QAResultSchema,
    Responsibility,
    Status,
    Urgency,
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
    issue_category: IssueCategory | None = None
    urgency: Urgency | None = None
    appliance_or_system: str | None = None
    issue_summary: str | None = None
    document_id: UUID | None = None

    # lease_check
    responsibility: Responsibility | None = None
    lease_addresses_issue: bool | None = None
    qa_results: list[QAResultSchema] = []

    # decide
    action_type: ActionType | None = None
    summary: str | None = None

    # draft
    draft: str | None = None

    # approval_gate
    approved: bool | None = None
    rejection_reason: str | None = None

    # bookkeeping
    status: Status = Status.IN_PROGRESS
    error: str | None = None
