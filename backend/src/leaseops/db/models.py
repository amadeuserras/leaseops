from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from leaseops.db.base import Base
from leaseops.models.schemas import EmailStatus


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(Text, nullable=True)


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processed', 'escalated')",
            name="emails_status_check",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    sender: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[EmailStatus] = mapped_column(Text, nullable=False)
