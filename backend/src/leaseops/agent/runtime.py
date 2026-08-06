from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import cast

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from leaseops.agent.checkpoint import CHECKPOINT_SERDE
from leaseops.agent.graph import build_graph
from leaseops.agent.runner import GraphRunner
from leaseops.db.session import require_database_url


def _psycopg_conninfo(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@asynccontextmanager
async def graph_runner() -> AsyncGenerator[GraphRunner]:
    conninfo = _psycopg_conninfo(require_database_url())
    async with AsyncConnectionPool(
        conninfo,
        min_size=1,
        max_size=10,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    ) as pool:
        checkpointer = AsyncPostgresSaver(
            conn=cast(AsyncConnectionPool[AsyncConnection[DictRow]], pool),
            serde=CHECKPOINT_SERDE,
        )
        await checkpointer.setup()
        yield GraphRunner(graph=build_graph(checkpointer))
