from __future__ import annotations

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# Custom enums/UUID types stored in checkpoints; without this allowlist,
# JsonPlusSerializer will (eventually) refuse to deserialize them from msgpack.
CHECKPOINT_SERDE = JsonPlusSerializer(
    allowed_msgpack_modules=[
        ("leaseops.agent.enums", "EmailCategory"),
        ("leaseops.agent.enums", "Severity"),
        ("leaseops.agent.enums", "Responsibility"),
        ("leaseops.agent.enums", "PlanAction"),
        ("leaseops.agent.schemas", "LeaseQaTool"),
        ("leaseops.agent.schemas", "SubmitVerdictTool"),
        ("leaseops.agent.schemas", "LeaseCheckStep"),
        ("asyncpg.pgproto.pgproto", "UUID"),
    ]
)
