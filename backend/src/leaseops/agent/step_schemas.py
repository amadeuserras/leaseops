from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, TypeAdapter

from leaseops.agent.state import (
    EmailCategory,
    PlanAction,
    QAResultSchema,
    Responsibility,
    Severity,
)
from leaseops.core.base import LeaseOpsModel


class ClassifyOutput(LeaseOpsModel):
    category: EmailCategory


class ExtractOutput(LeaseOpsModel):
    tenant_name: str | None
    unit: str | None
    address: str | None
    issue_summary: str | None
    severity: Severity | None
    appliance_or_system: str | None


class LeaseCheckOutput(LeaseOpsModel):
    lease_addresses_issue: bool
    responsibility: Responsibility
    qa_results: list[QAResultSchema]


class PlanOutput(LeaseOpsModel):
    actions: list[PlanAction]


class DraftOutput(LeaseOpsModel):
    draft: str


class ApprovalCard(LeaseOpsModel):
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


class ApprovalOutput(LeaseOpsModel):
    approved: bool


class ExecuteOutput(LeaseOpsModel):
    succeeded: bool


StepOutput = (
    ClassifyOutput
    | ExtractOutput
    | LeaseCheckOutput
    | PlanOutput
    | DraftOutput
    | ApprovalCard
    | ExecuteOutput
)


class StepBase(LeaseOpsModel):
    id: UUID
    run_id: UUID
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None
    created_at: datetime


class ClassifyStepResponse(StepBase):
    node_name: Literal["classify"]
    output: ClassifyOutput | None


class ExtractStepResponse(StepBase):
    node_name: Literal["extract"]
    output: ExtractOutput | None


class LeaseCheckStepResponse(StepBase):
    node_name: Literal["lease_check"]
    output: LeaseCheckOutput | None


class PlanStepResponse(StepBase):
    node_name: Literal["plan"]
    output: PlanOutput | None


class DraftStepResponse(StepBase):
    node_name: Literal["draft"]
    output: DraftOutput | None


class ApprovalStepResponse(StepBase):
    node_name: Literal["approval"]
    output: ApprovalCard | None


class ExecuteStepResponse(StepBase):
    node_name: Literal["execute"]
    output: ExecuteOutput | None


StepResponse = Annotated[
    ClassifyStepResponse
    | ExtractStepResponse
    | LeaseCheckStepResponse
    | PlanStepResponse
    | DraftStepResponse
    | ApprovalStepResponse
    | ExecuteStepResponse,
    Field(discriminator="node_name"),
]

StepResponseAdapter: TypeAdapter[StepResponse] = TypeAdapter(StepResponse)
