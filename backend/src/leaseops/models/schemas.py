from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class LeaseOpsModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class EmailStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    ESCALATED = "escalated"


class HealthResponse(LeaseOpsModel):
    status: str = "ok"
    service: str = "leaseops"
