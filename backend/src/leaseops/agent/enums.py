from __future__ import annotations

from enum import StrEnum


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
