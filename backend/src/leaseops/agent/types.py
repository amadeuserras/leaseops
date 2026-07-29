from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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
    REJECTED = "rejected"
    DONE = "done"


@dataclass(frozen=True)
class QAResultSchema:
    question: str
    answer: str
