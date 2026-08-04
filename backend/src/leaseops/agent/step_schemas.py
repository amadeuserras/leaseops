from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal, cast, get_args
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

ClassifyName = Literal["classify"]
ExtractName = Literal["extract"]
LeaseCheckName = Literal["lease_check"]
PlanName = Literal["plan"]
DraftName = Literal["draft"]
ApprovalName = Literal["approval"]
ExecuteName = Literal["execute"]

NodeName = (
    ClassifyName
    | ExtractName
    | LeaseCheckName
    | PlanName
    | DraftName
    | ApprovalName
    | ExecuteName
)


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
    reasoning: str | None = None


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

_OUTPUT_BY_NODE: dict[NodeName, type[LeaseOpsModel]] = {
    "classify": ClassifyOutput,
    "extract": ExtractOutput,
    "lease_check": LeaseCheckOutput,
    "plan": PlanOutput,
    "draft": DraftOutput,
    "approval": ApprovalCard,
    "execute": ExecuteOutput,
}

_NODE_NAMES = frozenset(
    name for member in get_args(NodeName) for name in get_args(member)
)


def parse_node_name(value: str) -> NodeName:
    if value not in _NODE_NAMES:
        raise ValueError(f"unknown node_name: {value}")
    return cast(NodeName, value)


def parse_step_output(node_name: NodeName, output: Any) -> StepOutput:
    return cast(StepOutput, _OUTPUT_BY_NODE[node_name].model_validate(output))


class StepBase(LeaseOpsModel):
    id: UUID
    run_id: UUID
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None
    created_at: datetime


class ClassifyStepResponse(StepBase):
    node_name: ClassifyName
    output: ClassifyOutput


class ExtractStepResponse(StepBase):
    node_name: ExtractName
    output: ExtractOutput


class LeaseCheckStepResponse(StepBase):
    node_name: LeaseCheckName
    output: LeaseCheckOutput


class PlanStepResponse(StepBase):
    node_name: PlanName
    output: PlanOutput


class DraftStepResponse(StepBase):
    node_name: DraftName
    output: DraftOutput


class ApprovalStepResponse(StepBase):
    node_name: ApprovalName
    output: ApprovalCard


class ExecuteStepResponse(StepBase):
    node_name: ExecuteName
    output: ExecuteOutput


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
