from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from leaseops.agent.runtime import graph_runner
from leaseops.api.approvals import router as approvals_router
from leaseops.api.runs import router as runs_router
from leaseops.api.work_orders import router as work_orders_router
from leaseops.core.logging import configure_logging
from leaseops.models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    configure_logging()
    async with graph_runner() as runner:
        app.state.runner = runner
        yield


app = FastAPI(title="LeaseOps", version="0.1.0", lifespan=lifespan)
app.include_router(work_orders_router)
app.include_router(runs_router)
app.include_router(approvals_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()
