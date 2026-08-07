from __future__ import annotations

from datetime import datetime
from uuid import UUID

from leaseops.agent.enums import (
    EmailCategory,
    PlanAction,
    Responsibility,
    Severity,
)
from leaseops.agent.schemas import LeaseCheckStep
from leaseops.core.base import LeaseOpsModel


class AgentState(LeaseOpsModel):
    # ingest
    email_id: UUID
    sender: str
    subject: str
    body: str
    received_at: datetime

    # classify
    category: EmailCategory | None = None

    # extract
    tenant_name: str | None = None
    unit: str | None = None
    address: str | None = None
    document_id: UUID | None = None
    issue_summary: str | None = None
    severity: Severity | None = None
    appliance_or_system: str | None = None

    # lease_check
    responsibility: Responsibility | None = None
    lease_addresses_issue: bool | None = None
    lease_check_steps: list[LeaseCheckStep] = []
    reasoning: str | None = None

    # draft
    draft: str | None = None

    # plan
    actions: list[PlanAction] = []

    # approval
    approved: bool | None = None

    # execute
    succeeded: bool = False
