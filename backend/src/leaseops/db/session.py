from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from leaseops.core.config import settings


def make_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url)


def make_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(make_engine(database_url), expire_on_commit=False)


engine = make_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
