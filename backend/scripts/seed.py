from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.core.config import settings
from leaseops.db.models import AuditLog, Email, Outbox, Run, Step, Tenant, WorkOrder
from leaseops.db.session import open_session, use_database
from leaseops.models.enums import EmailStatus

SEED_DIR = Path(__file__).resolve().parent.parent / "seed_data"

_DB_URLS = {
    "dev": settings.database_url,
    "evals": settings.evals_database_url,
    "tests": settings.test_database_url,
}


def _parse_database_url() -> tuple[str, str]:
    parser = argparse.ArgumentParser(
        description="Seed tenants and emails into a database."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--evals", action="store_const", const="evals", dest="target")
    group.add_argument("--tests", action="store_const", const="tests", dest="target")
    parser.set_defaults(target="dev")
    args = parser.parse_args()
    return args.target, _DB_URLS[args.target]


def load_json(name: str) -> list[dict[str, object]]:
    path = SEED_DIR / name
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise TypeError(f"{name} must be a JSON array")
    return data


def _tenant_from_row(row: dict[str, object]) -> Tenant:
    return Tenant(
        email=str(row["email"]),
        name=str(row["name"]),
        document_id=UUID(str(row["document_id"])),
        address=str(row["address"]),
        unit=str(row["unit"]) if row.get("unit") is not None else None,
    )


def _email_from_row(row: dict[str, object]) -> Email:
    return Email(
        sender=str(row["sender"]),
        subject=str(row["subject"]),
        body=str(row["body"]),
        received_at=datetime.fromisoformat(str(row["received_at"])),
        status=EmailStatus(str(row["status"])),
    )


async def _clear_tables(session: AsyncSession) -> None:
    await session.execute(delete(AuditLog))
    await session.execute(delete(Step))
    await session.execute(delete(Run))
    await session.execute(delete(Outbox))
    await session.execute(delete(WorkOrder))
    await session.execute(delete(Email))
    await session.execute(delete(Tenant))


async def seed(session: AsyncSession) -> tuple[int, int]:
    tenants = [_tenant_from_row(row) for row in load_json("tenants.json")]
    emails = [_email_from_row(row) for row in load_json("emails.json")]

    await _clear_tables(session)
    session.add_all(tenants)
    session.add_all(emails)
    await session.commit()
    return len(tenants), len(emails)


async def main() -> None:
    target, database_url = _parse_database_url()
    async with use_database(database_url), open_session() as session:
        n_tenants, n_emails = await seed(session)

    print(
        f"Seeded {n_tenants} tenant(s) and {n_emails} email(s) "
        f"into {target} from {SEED_DIR}"
    )


if __name__ == "__main__":
    asyncio.run(main())
