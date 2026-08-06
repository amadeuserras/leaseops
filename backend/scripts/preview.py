from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.core.config import settings
from leaseops.db.base import Base
from leaseops.db.models import AuditLog, Email, Outbox, Run, Step, Tenant, WorkOrder
from leaseops.db.session import open_session, use_database

MAX_ROWS = 4
MAX_CELL_WIDTH = 28
UUID_WIDTH = 8
SEPARATOR = " | "

_DB_URLS = {
    "dev": settings.database_url,
    "evals": settings.evals_database_url,
    "tests": settings.test_database_url,
}

MODELS: Sequence[type[Base]] = tuple(
    sorted(
        (AuditLog, Email, Outbox, Run, Step, Tenant, WorkOrder),
        key=lambda model: model.__tablename__,
    )
)


def _parse_database_url() -> tuple[str, str]:
    parser = argparse.ArgumentParser(description="Preview rows from a database.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--evals", action="store_const", const="evals", dest="target")
    group.add_argument("--tests", action="store_const", const="tests", dest="target")
    parser.set_defaults(target="dev")
    args = parser.parse_args()
    return args.target, _DB_URLS[args.target]


def _is_uuid_column(dtype: str) -> bool:
    return dtype.upper() == "UUID"


def format_header(name: str, dtype: str) -> str:
    if _is_uuid_column(dtype):
        return name
    base = dtype.split("(", 1)[0].upper()
    short = {
        "TEXT": "txt",
        "JSONB": "json",
        "INTEGER": "int",
        "DATETIME": "ts",
        "NUMERIC": "num",
    }.get(base, base.lower())
    return f"{name} ({short})"


def format_cell(value: object, *, dtype: str) -> str:
    if value is None:
        return "NULL"
    if _is_uuid_column(dtype) or isinstance(value, UUID):
        return str(value)[:UUID_WIDTH]
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    text = str(value).replace("\n", "\\n")
    if len(text) > MAX_CELL_WIDTH:
        return f"{text[: MAX_CELL_WIDTH - 3]}..."
    return text


def print_table(
    table: str,
    columns: list[tuple[str, str]],
    rows: Sequence[object],
    total_rows: int,
) -> None:
    headers = [format_header(name, dtype) for name, dtype in columns]
    rendered = [
        [format_cell(getattr(row, name), dtype=dtype) for name, dtype in columns]
        for row in rows
    ]
    widths = []
    for i, _ in enumerate(columns):
        if rendered:
            width = max(len(headers[i]), *(len(r[i]) for r in rendered))
        else:
            width = len(headers[i])
        widths.append(width)

    print(f"\n=== {table} ({total_rows} rows) ===")
    print(SEPARATOR.join(h.ljust(w) for h, w in zip(headers, widths, strict=True)))
    print("-+-".join("-" * w for w in widths))
    if not rows:
        print("  (no rows)")
        return
    for rendered_row in rendered:
        print(
            SEPARATOR.join(cell.ljust(widths[i]) for i, cell in enumerate(rendered_row))
        )


async def preview_model(session: AsyncSession, model: type[Base]) -> None:
    columns = [(column.name, str(column.type)) for column in model.__table__.columns]
    total_rows = await session.scalar(select(func.count()).select_from(model)) or 0
    rows = list((await session.scalars(select(model).limit(MAX_ROWS))).all())
    print_table(model.__tablename__, columns, rows, total_rows)


async def main() -> None:
    target, database_url = _parse_database_url()
    print(f"Previewing {target} database")
    async with use_database(database_url), open_session() as session:
        if not MODELS:
            print("No mapped models.")
            return
        for model in MODELS:
            await preview_model(session, model)


if __name__ == "__main__":
    asyncio.run(main())
