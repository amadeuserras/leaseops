from __future__ import annotations

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# Custom enums/UUID types stored in checkpoints; without this allowlist,
# JsonPlusSerializer will (eventually) refuse to deserialize them from msgpack.
CHECKPOINT_SERDE = JsonPlusSerializer(
    allowed_msgpack_modules=[
        ("leaseops.agent.state", "Status"),
        ("leaseops.agent.state", "EmailCategory"),
        ("leaseops.agent.state", "IssueCategory"),
        ("leaseops.agent.state", "Urgency"),
        ("leaseops.agent.state", "Responsibility"),
        ("leaseops.agent.state", "ActionType"),
        ("asyncpg.pgproto.pgproto", "UUID"),
    ]
)
