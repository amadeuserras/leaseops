from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from leaseops.models.schemas import LeaseOpsModel


class EmailCategory(StrEnum):
    MAINTENANCE = "maintenance"
    LEASE_QUESTION = "lease_question"
    NOT_OUR_PROBLEM = "not_our_problem"
    EMERGENCY = "emergency"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Responsibility(StrEnum):
    LANDLORD = "landlord"
    TENANT = "tenant"
    SHARED = "shared"
    UNCLEAR = "unclear"


class PlanAction(StrEnum):
    SEND_REPLY = "send_reply"
    CREATE_WORK_ORDER = "create_work_order"
    CALL_TENANT = "call_tenant"


@dataclass(frozen=True)
class QAResultSchema:
    question: str
    answer: str
    citations: list[str]


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

    # execute
    actions_taken: list[PlanAction] = []
