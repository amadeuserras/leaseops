from __future__ import annotations

import asyncio
import shutil

import asyncpg

from leaseops.core.config import settings

MAX_ROWS = 4
MAX_CELL_WIDTH = 48
SEPARATOR = " | "


def asyncpg_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def list_tables(conn: asyncpg.Connection) -> list[str]:
    rows = await conn.fetch(
        """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
        """
    )
    return [row["tablename"] for row in rows]


async def list_columns(conn: asyncpg.Connection, table: str) -> list[tuple[str, str]]:
    rows = await conn.fetch(
        """
        SELECT
            a.attname AS column_name,
            pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
        JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = 'public'
          AND c.relname = $1
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY a.attnum
        """,
        table,
    )
    return [(row["column_name"], row["data_type"]) for row in rows]


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
    rows: list[asyncpg.Record],
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

    rendered = [[format_cell(row[name]) for name in column_names] for row in rows]
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
                print(f"{header}: {format_cell(row[name])}")
        return

    print(SEPARATOR.join(h.ljust(w) for h, w in zip(headers, widths, strict=True)))
    print("-+-".join("-" * w for w in widths))
    for rendered_row in rendered:
        print(
            SEPARATOR.join(cell.ljust(widths[i]) for i, cell in enumerate(rendered_row))
        )


async def main() -> None:
    conn = await asyncpg.connect(asyncpg_url(settings.database_url))
    try:
        tables = await list_tables(conn)
        if not tables:
            print("No tables in public schema.")
            return

        for table in tables:
            columns = await list_columns(conn, table)
            total_rows = await conn.fetchval(f'SELECT COUNT(*) FROM "{table}"')
            rows = await conn.fetch(f'SELECT * FROM "{table}" LIMIT {MAX_ROWS}')
            print_table(table, columns, rows, total_rows)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
