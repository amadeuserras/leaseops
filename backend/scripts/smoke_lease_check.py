from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from uuid import UUID, uuid4

from leaseops.agent.lease_check import lease_check
from leaseops.agent.state import (
    AgentState,
    EmailCategory,
    IssueCategory,
    Urgency,
)

MOCK_STATE = AgentState(
    email_id=uuid4(),
    sender="deshawn.johnson@example.com",
    subject="Kitchen sink leaking again",
    body=(
        "Hi, the kitchen sink under the cabinet is dripping steadily since "
        "yesterday. Can someone take a look?"
    ),
    category=EmailCategory.MAINTENANCE,
    tenant_name="DeShawn Johnson",
    unit="5",
    address="1142 Sunset Ridge Drive, Los Angeles, CA 90026",
    issue_category=IssueCategory.PLUMBING,
    urgency=Urgency.MEDIUM,
    appliance_or_system="kitchen sink",
    issue_summary=(
        "Kitchen sink under the cabinet has been dripping steadily for "
        "approximately one day; no cause stated."
    ),
    document_id=UUID("c20c63ab-9330-40ce-af05-8dd84c545803"),
)


async def main() -> None:
    result = await lease_check(MOCK_STATE)
    print(json.dumps(asdict(result), indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
