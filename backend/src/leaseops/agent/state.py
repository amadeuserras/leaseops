from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from leaseops.models.schemas import LeaseOpsModel


class EmailCategory(StrEnum):
    MAINTENANCE = "maintenance"
    LEASE_QUESTION = "lease_question"
    NOT_OUR_PROBLEM = "not_our_problem"
    EMERGENCY = "emergency"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class IssueCategory(StrEnum):
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    APPLIANCE = "appliance"
    STRUCTURAL = "structural"
    PEST = "pest"
    ACCESS = "access"
    OTHER = "other"


class Responsibility(StrEnum):
    LANDLORD = "landlord"
    TENANT = "tenant"
    SHARED = "shared"
    UNCLEAR = "unclear"


class ActionType(StrEnum):
    CREATE_WORK_ORDER = "create_work_order"
    SEND_REPLY = "send_reply"
    ESCALATE = "escalate"
    NO_ACTION = "no_action"


class Status(StrEnum):
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    DONE = "done"


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

    # lease_check
    responsibility: Responsibility | None = None
    question_asked: str | None = None
    answer: str | None = None

    # decide
    action_type: ActionType | None = None
    summary: str | None = None

    # draft
    draft: str | None = None

    # bookkeeping
    status: Status = Status.IN_PROGRESS
    error: str | None = None
