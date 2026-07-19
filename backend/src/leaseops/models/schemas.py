from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LeaseOpsModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class HealthResponse(LeaseOpsModel):
    status: str = "ok"
    service: str = "leaseops"
