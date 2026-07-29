from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from uuid import UUID, uuid4

from leaseops.agent.draft import draft
from leaseops.agent.state import AgentState
from leaseops.agent.types import (
    ActionType,
    EmailCategory,
    IssueCategory,
    QAResultSchema,
    Responsibility,
    Urgency,
)

MOCK_LANDLORD = AgentState(
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
    responsibility=Responsibility.LANDLORD,
    lease_addresses_issue=True,
    qa_results=[
        QAResultSchema(
            question=(
                "Who is responsible for repair and maintenance of the "
                "kitchen plumbing fixtures?"
            ),
            answer=(
                "The landlord is responsible for maintaining plumbing "
                "fixtures in good working order [Section 12.1 — Repairs "
                "and Maintenance]."
            ),
        )
    ],
    action_type=ActionType.CREATE_WORK_ORDER,
    summary="Lease assigns repair responsibility to the landlord.",
)

MOCK_TENANT = AgentState(
    email_id=uuid4(),
    sender="deshawn.johnson@example.com",
    subject="Fix my dishwasher already",
    body=(
        "This is ridiculous. The dishwasher has been broken for a week and "
        "I keep getting ignored. I pay rent on time — someone better come "
        "fix it today or I'm done dealing with this nonsense."
    ),
    category=EmailCategory.MAINTENANCE,
    tenant_name="DeShawn Johnson",
    unit="5",
    address="1142 Sunset Ridge Drive, Los Angeles, CA 90026",
    issue_category=IssueCategory.APPLIANCE,
    urgency=Urgency.MEDIUM,
    appliance_or_system="dishwasher",
    issue_summary=(
        "Dishwasher reported broken for approximately one week; tenant requests repair."
    ),
    document_id=UUID("c20c63ab-9330-40ce-af05-8dd84c545803"),
    responsibility=Responsibility.TENANT,
    lease_addresses_issue=True,
    qa_results=[
        QAResultSchema(
            question=(
                "Who is responsible for repair and maintenance of "
                "appliances provided with the unit?"
            ),
            answer=(
                "The tenant is responsible for routine care and for repair "
                "costs arising from misuse or negligence of appliances "
                "[Section 9.3 — Appliances]."
            ),
        )
    ],
    action_type=ActionType.SEND_REPLY,
    summary="Lease assigns responsibility to the tenant; explain and close.",
)


async def main() -> None:
    for label, state in (("tenant", MOCK_TENANT),):
        result = await draft(state)
        print(f"=== {label} ===")
        print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
