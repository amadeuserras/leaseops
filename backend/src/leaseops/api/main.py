from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from leaseops.api.work_orders import router as work_orders_router
from leaseops.core.logging import configure_logging
from leaseops.models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    configure_logging()
    yield


app = FastAPI(title="LeaseOps", version="0.1.0", lifespan=lifespan)
app.include_router(work_orders_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()
