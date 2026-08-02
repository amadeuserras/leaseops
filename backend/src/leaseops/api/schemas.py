from __future__ import annotations

from datetime import datetime
from uuid import UUID

from leaseops.core.base import LeaseOpsModel
from leaseops.models.enums import EmailStatus, OutboxStatus, RunStatus, WorkOrderStatus


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
    unit: str | None = None
    severity: str | None = None
    actions_taken: list[str] = []


class EmailListResponse(LeaseOpsModel):
    items: list[EmailResponse]
    agent_last_ran_at: datetime | None = None


class RunCreate(LeaseOpsModel):
    email_id: UUID


class RunResponse(LeaseOpsModel):
    id: UUID
    email_id: UUID
    status: RunStatus
    started_at: datetime
    ended_at: datetime | None


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
