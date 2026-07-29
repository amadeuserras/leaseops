from __future__ import annotations

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# Custom enums/UUID types stored in checkpoints; without this allowlist,
# JsonPlusSerializer will (eventually) refuse to deserialize them from msgpack.
CHECKPOINT_SERDE = JsonPlusSerializer(
    allowed_msgpack_modules=[
        ("leaseops.agent.types", "Status"),
        ("leaseops.agent.types", "EmailCategory"),
        ("leaseops.agent.types", "IssueCategory"),
        ("leaseops.agent.types", "Urgency"),
        ("leaseops.agent.types", "Responsibility"),
        ("leaseops.agent.types", "ActionType"),
        ("asyncpg.pgproto.pgproto", "UUID"),
    ]
)
