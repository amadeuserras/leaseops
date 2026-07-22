from __future__ import annotations

import asyncio
import shutil
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from leaseops.core.config import settings
from leaseops.db.base import Base
from leaseops.db.models import AuditLog, Email, Outbox, Run, Step, Tenant, WorkOrder

MAX_ROWS = 4
MAX_CELL_WIDTH = 48
SEPARATOR = " | "

MODELS: Sequence[type[Base]] = tuple(
    sorted(
        (AuditLog, Email, Outbox, Run, Step, Tenant, WorkOrder),
        key=lambda model: model.__tablename__,
    )
)


def format_cell(value: object) -> str:
    if value is None:
        return "NULL"
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
    headers = [f"{name} ({dtype})" for name, dtype in columns]
    column_names = [name for name, _ in columns]

    print(f"\n=== {table} ({total_rows} rows) ===")
    if not rows:
        for header in headers:
            print(f"  {header}")
        print("  (no rows)")
        return

    rendered = [
        [format_cell(getattr(row, name)) for name in column_names] for row in rows
    ]
    widths = [
        min(
            max(len(headers[i]), *(len(r[i]) for r in rendered)),
            MAX_CELL_WIDTH,
        )
        for i in range(len(headers))
    ]
    term_width = max(40, shutil.get_terminal_size((100, 24)).columns)
    if sum(widths) + len(SEPARATOR) * (len(widths) - 1) > term_width:
        for i, row in enumerate(rows, start=1):
            print(f"\n--- row {i} ---")
            for header, name in zip(headers, column_names, strict=True):
                print(f"{header}: {format_cell(getattr(row, name))}")
        return

    print(SEPARATOR.join(h.ljust(w) for h, w in zip(headers, widths, strict=True)))
    print("-+-".join("-" * w for w in widths))
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
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            if not MODELS:
                print("No mapped models.")
                return
            for model in MODELS:
                await preview_model(session, model)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
