from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_factory: async_sessionmaker[AsyncSession] | None = None
_engine: AsyncEngine | None = None
_database_url: str | None = None


def make_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url)


def require_database_url() -> str:
    if _database_url is None:
        raise RuntimeError(
            "Database not configured. Wrap the entry point with "
            "use_database(url) before opening a session."
        )
    return _database_url


def _require_factory() -> async_sessionmaker[AsyncSession]:
    if _factory is None:
        raise RuntimeError(
            "Database not configured. Wrap the entry point with "
            "use_database(url) before opening a session."
        )
    return _factory


@asynccontextmanager
async def use_database(database_url: str) -> AsyncGenerator[None]:
    """Bind the process DB for this block. Required before open_session()."""
    global _factory, _engine, _database_url
    if _factory is not None:
        raise RuntimeError("Database already configured")
    _database_url = database_url
    _engine = make_engine(database_url)
    _factory = async_sessionmaker(_engine, expire_on_commit=False)
    try:
        yield
    finally:
        _factory = None
        _database_url = None
        await _engine.dispose()
        _engine = None


@asynccontextmanager
async def open_session() -> AsyncGenerator[AsyncSession]:
    """Open a short-lived session (langgraph nodes and scripts)."""
    async with _require_factory()() as session:
        yield session


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI Depends wrapper around open_session()."""
    async with open_session() as session:
        yield session
