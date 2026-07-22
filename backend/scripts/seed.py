from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from leaseops.core.config import settings
from leaseops.db.models import Email, Tenant
from leaseops.models.schemas import EmailStatus

SEED_DIR = Path(__file__).resolve().parent.parent / "seed_data"


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
        property_address=str(row["property_address"]),
    )


def _email_from_row(row: dict[str, object]) -> Email:
    return Email(
        sender=str(row["sender"]),
        subject=str(row["subject"]),
        body=str(row["body"]),
        received_at=datetime.fromisoformat(str(row["received_at"])),
        status=EmailStatus(str(row["status"])),
    )


async def seed(session: AsyncSession) -> tuple[int, int]:
    tenants = [_tenant_from_row(row) for row in load_json("tenants.json")]
    emails = [_email_from_row(row) for row in load_json("emails.json")]

    await session.execute(delete(Email))
    await session.execute(delete(Tenant))
    session.add_all(tenants)
    session.add_all(emails)
    await session.commit()
    return len(tenants), len(emails)


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            n_tenants, n_emails = await seed(session)
    finally:
        await engine.dispose()

    print(f"Seeded {n_tenants} tenant(s) and {n_emails} email(s) from {SEED_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
