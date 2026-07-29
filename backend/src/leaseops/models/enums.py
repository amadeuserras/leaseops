from __future__ import annotations

from enum import StrEnum


class EmailStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    ESCALATED = "escalated"


class WorkOrderStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class OutboxStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class RunStatus(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    DONE = "done"
    FAILED = "failed"
