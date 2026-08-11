from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.core.config import settings
from leaseops.db.models import (
    AuditLog,
    DemoSession,
    Email,
    Outbox,
    Run,
    Step,
    Tenant,
    WorkOrder,
)
from leaseops.db.session import open_session, use_database

SEED_DIR = Path(__file__).resolve().parent.parent / "seed_data"

_DB_URLS = {
    "dev": settings.database_url,
    "evals": settings.evals_database_url,
    "tests": settings.test_database_url,
}


def _parse_database_url() -> tuple[str, str]:
    parser = argparse.ArgumentParser(
        description="Seed shared tenants. Demo inboxes are cloned per visitor session."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--evals", action="store_const", const="evals", dest="target")
    group.add_argument("--tests", action="store_const", const="tests", dest="target")
    parser.set_defaults(target="dev")
    args = parser.parse_args()
    return args.target, _DB_URLS[args.target]


def load_tenants() -> list[Tenant]:
    path = SEED_DIR / "tenants.json"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise TypeError("tenants.json must be a JSON array")
    return [
        Tenant(
            email=str(row["email"]),
            name=str(row["name"]),
            document_id=UUID(str(row["document_id"])),
            address=str(row["address"]),
            unit=str(row["unit"]) if row.get("unit") is not None else None,
        )
        for row in data
    ]


async def _clear_tables(session: AsyncSession) -> None:
    await session.execute(delete(AuditLog))
    await session.execute(delete(Step))
    await session.execute(delete(Run))
    await session.execute(delete(Outbox))
    await session.execute(delete(WorkOrder))
    await session.execute(delete(Email))
    await session.execute(delete(DemoSession))
    await session.execute(delete(Tenant))


async def seed(session: AsyncSession) -> int:
    tenants = load_tenants()
    await _clear_tables(session)
    session.add_all(tenants)
    await session.commit()
    return len(tenants)


async def main() -> None:
    target, database_url = _parse_database_url()
    async with use_database(database_url), open_session() as session:
        n_tenants = await seed(session)

    print(f"Seeded {n_tenants} tenant(s) into {target} from {SEED_DIR}")
    print("Demo inboxes are created by POST /sessions (one fresh copy per visitor).")


if __name__ == "__main__":
    asyncio.run(main())
