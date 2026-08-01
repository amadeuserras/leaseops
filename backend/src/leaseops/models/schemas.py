from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from leaseops.models.enums import EmailStatus, OutboxStatus, RunStatus, WorkOrderStatus


class LeaseOpsModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class HealthResponse(LeaseOpsModel):
    status: str = "ok"
    service: str = "leaseops"


class EmailCreate(LeaseOpsModel):
    sender: str
    subject: str
    body: str
    received_at: datetime
    status: EmailStatus = EmailStatus.PENDING


class EmailResponse(LeaseOpsModel):
    id: UUID
    sender: str
    subject: str
    body: str
    received_at: datetime
    status: EmailStatus


class EmailListResponse(LeaseOpsModel):
    items: list[EmailResponse]


class RunCreate(LeaseOpsModel):
    email_id: UUID


class RunResponse(LeaseOpsModel):
    id: UUID
    email_id: UUID
    status: RunStatus
    started_at: datetime
    ended_at: datetime | None


class StepResponse(LeaseOpsModel):
    id: UUID
    run_id: UUID
    node_name: str
    output: dict[str, Any] | None
    tokens: int | None
    cost_usd: float | None
    created_at: datetime


class StepListResponse(LeaseOpsModel):
    items: list[StepResponse]


class ApprovalRequestResponse(LeaseOpsModel):
    run_id: UUID
    email_id: UUID
    category: str
    severity: str | None
    received_at: str
    tenant_name: str | None
    unit: str | None
    address: str | None
    issue_summary: str | None
    appliance_or_system: str | None
    responsibility: str | None
    citation: str | None
    original_email: str
    draft: str | None
    actions: list[str]


class ApprovalListResponse(LeaseOpsModel):
    items: list[ApprovalRequestResponse]


class WorkOrderCreate(LeaseOpsModel):
    email_id: UUID
    tenant_id: UUID
    issue: str
    status: WorkOrderStatus = WorkOrderStatus.OPEN


class WorkOrderUpdate(LeaseOpsModel):
    issue: str | None = None
    status: WorkOrderStatus | None = None


class WorkOrderResponse(LeaseOpsModel):
    id: UUID
    email_id: UUID
    tenant_id: UUID
    issue: str
    status: WorkOrderStatus
    created_at: datetime


class WorkOrderListResponse(LeaseOpsModel):
    items: list[WorkOrderResponse]


class TenantResponse(LeaseOpsModel):
    id: UUID
    email: str
    name: str
    document_id: UUID
    address: str
    unit: str | None


class OutboxCreate(LeaseOpsModel):
    email_id: UUID
    draft_text: str
    status: OutboxStatus = OutboxStatus.DRAFT


class OutboxResponse(LeaseOpsModel):
    id: UUID
    email_id: UUID
    draft_text: str
    status: OutboxStatus
    created_at: datetime


class LeaseQAResponse(LeaseOpsModel):
    answer: str
