from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker

import leaseops.db.models  # noqa: F401
from leaseops.core.config import settings
from leaseops.db.base import Base
from leaseops.db.session import make_engine


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
    async with session_factory() as session:
        yield session
