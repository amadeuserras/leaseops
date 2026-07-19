from __future__ import annotations

from fastapi import FastAPI

from leaseops.models.schemas import HealthResponse

app = FastAPI(title="LeaseOps", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()
