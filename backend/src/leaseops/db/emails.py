from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.api.schemas import EmailCreate
from leaseops.db.models import Email, Run, Step, Tenant
from leaseops.models.enums import EmailStatus


def _empty_actions() -> list[str]:
    return []


@dataclass(frozen=True)
class InboxRow:
    email: Email
    unit: str | None = None
    severity: str | None = None
    actions_taken: list[str] = field(default_factory=_empty_actions)


def _severity_from_output(output: dict[str, Any] | None) -> str | None:
    if output is None:
        return None
    severity = output.get("severity")
    return str(severity) if severity is not None else None


def _actions_from_output(output: dict[str, Any] | None) -> list[str]:
    if output is None:
        return []
    raw = cast(list[Any], output.get("actions") or [])
    return [str(action) for action in raw]


def _execute_succeeded(output: dict[str, Any] | None) -> bool:
    return bool(output and output.get("succeeded") is True)


def _actions_taken(
    *,
    planned: list[str],
    executed: bool,
) -> list[str]:
    return planned if executed else []


async def create_email(
    session: AsyncSession,
    payload: EmailCreate,
    *,
    session_id: UUID,
) -> Email:
    email = Email(
        session_id=session_id,
        sender=payload.sender,
        subject=payload.subject,
        body=payload.body,
        received_at=payload.received_at,
        status=payload.status,
    )
    session.add(email)
    await session.commit()
    await session.refresh(email)
    return email


async def list_emails(
    session: AsyncSession,
    *,
    session_id: UUID,
    status: EmailStatus | None = None,
) -> list[Email]:
    stmt = (
        select(Email)
        .where(Email.session_id == session_id)
        .order_by(Email.received_at.desc())
    )
    if status is not None:
        stmt = stmt.where(Email.status == status)
    return list((await session.scalars(stmt)).all())


async def list_inbox_rows(
    session: AsyncSession,
    *,
    session_id: UUID,
    status: EmailStatus | None = None,
) -> list[InboxRow]:
    stmt = (
        select(Email, Tenant.unit)
        .outerjoin(
            Tenant,
            Tenant.email == func.lower(func.trim(Email.sender)),
        )
        .where(Email.session_id == session_id)
        .order_by(Email.received_at.desc())
    )
    if status is not None:
        stmt = stmt.where(Email.status == status)

    rows = (await session.execute(stmt)).all()
    if not rows:
        return []

    emails = [row[0] for row in rows]
    unit_by_email_id = {row[0].id: row[1] for row in rows}
    email_ids = [email.id for email in emails]

    latest_runs = (
        await session.execute(
            select(Run.id, Run.email_id)
            .where(Run.email_id.in_(email_ids))
            .distinct(Run.email_id)
            .order_by(Run.email_id, Run.started_at.desc())
        )
    ).all()
    run_id_by_email_id = {email_id: run_id for run_id, email_id in latest_runs}
    run_ids = list(run_id_by_email_id.values())

    severity_by_email_id: dict[UUID, str | None] = {}
    planned_by_email_id: dict[UUID, list[str]] = {}
    executed_by_email_id: dict[UUID, bool] = {}
    if run_ids:
        steps = (
            await session.scalars(
                select(Step).where(
                    Step.run_id.in_(run_ids),
                    Step.node_name.in_(("extract", "plan", "execute")),
                )
            )
        ).all()
        email_id_by_run_id = {
            run_id: email_id for email_id, run_id in run_id_by_email_id.items()
        }
        for step in steps:
            email_id = email_id_by_run_id[step.run_id]
            if step.node_name == "extract":
                severity_by_email_id[email_id] = _severity_from_output(step.output)
            elif step.node_name == "plan":
                planned_by_email_id[email_id] = _actions_from_output(step.output)
            elif step.node_name == "execute":
                executed_by_email_id[email_id] = _execute_succeeded(step.output)

    return [
        InboxRow(
            email=email,
            unit=unit_by_email_id.get(email.id),
            severity=severity_by_email_id.get(email.id),
            actions_taken=_actions_taken(
                planned=planned_by_email_id.get(email.id, []),
                executed=executed_by_email_id.get(email.id, False),
            ),
        )
        for email in emails
    ]


async def get_email_by_id(
    session: AsyncSession,
    email_id: UUID,
    *,
    session_id: UUID | None = None,
) -> Email | None:
    email = await session.get(Email, email_id)
    if email is None:
        return None
    if session_id is not None and email.session_id != session_id:
        return None
    return email


async def get_inbox_row(
    session: AsyncSession,
    email_id: UUID,
    *,
    session_id: UUID | None = None,
) -> InboxRow | None:
    email = await get_email_by_id(session, email_id, session_id=session_id)
    if email is None:
        return None

    unit = await session.scalar(
        select(Tenant.unit).where(Tenant.email == func.lower(func.trim(email.sender)))
    )

    latest_run_id = await session.scalar(
        select(Run.id)
        .where(Run.email_id == email_id)
        .order_by(Run.started_at.desc())
        .limit(1)
    )

    severity: str | None = None
    planned: list[str] = []
    executed = False
    if latest_run_id is not None:
        steps = (
            await session.scalars(
                select(Step).where(
                    Step.run_id == latest_run_id,
                    Step.node_name.in_(("extract", "plan", "execute")),
                )
            )
        ).all()
        for step in steps:
            if step.node_name == "extract":
                severity = _severity_from_output(step.output)
            elif step.node_name == "plan":
                planned = _actions_from_output(step.output)
            elif step.node_name == "execute":
                executed = _execute_succeeded(step.output)

    return InboxRow(
        email=email,
        unit=unit,
        severity=severity,
        actions_taken=_actions_taken(planned=planned, executed=executed),
    )


async def get_email_by_subject(session: AsyncSession, subject: str) -> Email | None:
    result = await session.scalars(
        select(Email)
        .where(Email.subject == subject)
        .order_by(Email.received_at.desc())
        .limit(1)
    )
    return result.first()


async def set_email_status(
    session: AsyncSession, email_id: UUID, status: EmailStatus
) -> Email:
    email = await session.get(Email, email_id)
    if email is None:
        raise LookupError(f"email not found: {email_id}")
    email.status = status
    await session.commit()
    await session.refresh(email)
    return email
