from __future__ import annotations

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

import leaseops.db.models  # noqa: F401
from leaseops.agent.runner import GraphRunner
from leaseops.api.approvals import router as approvals_router
from leaseops.api.inbox import router as inbox_router
from leaseops.api.runs import router as runs_router
from leaseops.api.sessions import router as sessions_router
from leaseops.api.work_orders import router as work_orders_router
from leaseops.core.config import settings
from leaseops.db import demo_sessions as demo_sessions_repo
from leaseops.db.base import Base
from leaseops.db.models import DemoSession
from leaseops.db.session import get_session, make_engine, use_database


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = make_engine(settings.test_database_url)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with (
        use_database(settings.test_database_url),
        session_factory() as session,
    ):
        yield session


@pytest_asyncio.fixture
async def demo_session(db_session) -> DemoSession:
    return await demo_sessions_repo.create_empty_session(db_session)


@pytest_asyncio.fixture
async def runner() -> GraphRunner:
    return GraphRunner(graph=None)


@pytest_asyncio.fixture
async def api_client(db_session, runner, demo_session):
    app = FastAPI()
    app.state.runner = runner
    app.include_router(sessions_router)
    app.include_router(inbox_router)
    app.include_router(work_orders_router)
    app.include_router(runs_router)
    app.include_router(approvals_router)

    async def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Session-Id": str(demo_session.id)},
    ) as client:
        yield client
