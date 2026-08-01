from __future__ import annotations

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# Custom enums/UUID types stored in checkpoints; without this allowlist,
# JsonPlusSerializer will (eventually) refuse to deserialize them from msgpack.
CHECKPOINT_SERDE = JsonPlusSerializer(
    allowed_msgpack_modules=[
        ("leaseops.agent.state", "EmailCategory"),
        ("leaseops.agent.state", "Severity"),
        ("leaseops.agent.state", "Responsibility"),
        ("leaseops.agent.state", "PlanAction"),
        ("leaseops.agent.state", "QAResultSchema"),
        ("asyncpg.pgproto.pgproto", "UUID"),
    ]
)
