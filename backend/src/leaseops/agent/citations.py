from __future__ import annotations

import re

from leaseops.agent.schemas import LeaseCheckStep, LeaseQaTool

# Matches inline citation ids as they appear in answers.
# Copied from leaseclear.evals.generation.answer.
CITATION_ID_RE = re.compile(r"\[([a-z0-9-]+) (§[^\]]+|p\d+(?:\(\d+\))?)\]")


def extract_citation_ids(text: str) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for match in CITATION_ID_RE.finditer(text):
        citation_id = match.group(0)
        if citation_id not in seen:
            seen.add(citation_id)
            ids.append(citation_id)
    return ids


def first_citation(steps: list[LeaseCheckStep]) -> str | None:
    """Card display: first citation on the earliest lease_qa that has one."""
    for step in steps:
        tool = step.tool
        if isinstance(tool, LeaseQaTool) and tool.citations:
            return tool.citations[0]
    return None
