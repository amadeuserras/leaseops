from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from langgraph.config import get_stream_writer

from leaseops.agent.step_schemas import ApprovalCard

_PRICING_PER_TOKEN_USD: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15 / 1_000_000, 0.60 / 1_000_000),
    "claude-sonnet-4-5": (3.00 / 1_000_000, 15.00 / 1_000_000),
}


@dataclass(frozen=True, kw_only=True)
class RunStartedEvent:
    type: Literal["run_started"] = "run_started"
    run_id: str


@dataclass(frozen=True, kw_only=True)
class NodeStartedEvent:
    type: Literal["node_started"] = "node_started"
    node: str


@dataclass(frozen=True, kw_only=True)
class NodeFinishedEvent:
    type: Literal["node_finished"] = "node_finished"
    node: str
    output: Any


@dataclass(frozen=True, kw_only=True)
class PausedEvent:
    type: Literal["paused"] = "paused"
    request: ApprovalCard


@dataclass(frozen=True, kw_only=True)
class ErrorEvent:
    type: Literal["error"] = "error"
    message: str


@dataclass(frozen=True, kw_only=True)
class RunFinishedEvent:
    type: Literal["run_finished"] = "run_finished"
    status: str


@dataclass(frozen=True, kw_only=True)
class ToolCallEvent:
    type: Literal["tool_call"] = "tool_call"
    node: str
    tool: str
    arguments: dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class ToolResultEvent:
    type: Literal["tool_result"] = "tool_result"
    node: str
    tool: str
    result: Any
    is_error: bool = False


@dataclass(frozen=True, kw_only=True)
class CostEvent:
    type: Literal["cost"] = "cost"
    node: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


StreamEvent = (
    RunStartedEvent
    | NodeStartedEvent
    | NodeFinishedEvent
    | PausedEvent
    | ErrorEvent
    | RunFinishedEvent
    | ToolCallEvent
    | ToolResultEvent
    | CostEvent
)


def _emit(event: StreamEvent) -> None:
    writer = get_stream_writer()
    writer(asdict(event))


def emit_tool_call(node: str, tool: str, arguments: dict[str, Any]) -> None:
    _emit(ToolCallEvent(node=node, tool=tool, arguments=arguments))


def emit_tool_result(
    node: str, tool: str, result: Any, *, is_error: bool = False
) -> None:
    _emit(ToolResultEvent(node=node, tool=tool, result=result, is_error=is_error))


def emit_cost(node: str, model: str, input_tokens: int, output_tokens: int) -> None:
    input_price, output_price = _PRICING_PER_TOKEN_USD.get(model, (0.0, 0.0))
    cost_usd = input_tokens * input_price + output_tokens * output_price
    _emit(
        CostEvent(
            node=node,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
    )
