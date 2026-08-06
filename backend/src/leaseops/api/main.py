from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from leaseops.agent.runtime import graph_runner
from leaseops.api.approvals import router as approvals_router
from leaseops.api.inbox import router as inbox_router
from leaseops.api.runs import router as runs_router
from leaseops.api.schemas import HealthResponse
from leaseops.api.work_orders import router as work_orders_router
from leaseops.core.config import settings
from leaseops.core.logging import configure_logging
from leaseops.db.session import use_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    configure_logging()
    async with (
        use_database(settings.database_url),
        graph_runner() as runner,
    ):
        app.state.runner = runner
        yield


app = FastAPI(title="LeaseOps", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(inbox_router)
app.include_router(work_orders_router)
app.include_router(runs_router)
app.include_router(approvals_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()
