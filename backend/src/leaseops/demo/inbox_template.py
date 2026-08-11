from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, cast

from leaseops.models.enums import EmailStatus

_INBOX_PATH = Path(__file__).resolve().parent / "emails.json"


class InboxTemplateRow(TypedDict):
    sender: str
    subject: str
    body: str
    received_at: datetime
    status: EmailStatus


def load_inbox_template() -> list[InboxTemplateRow]:
    with _INBOX_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    rows: list[InboxTemplateRow] = []
    for raw in cast(list[Any], data):
        row = cast(dict[str, Any], raw)
        rows.append(
            {
                "sender": str(row["sender"]),
                "subject": str(row["subject"]),
                "body": str(row["body"]),
                "received_at": datetime.fromisoformat(str(row["received_at"])),
                "status": EmailStatus(str(row.get("status", EmailStatus.PENDING))),
            }
        )
    return rows
