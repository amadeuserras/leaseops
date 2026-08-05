"""Run the evals pipeline against the golden dataset.

Usage:
    uv run python scripts/run_evals.py
    uv run python scripts/run_evals.py --limit 3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
from datetime import UTC, datetime
from pathlib import Path

from pydantic import TypeAdapter

from leaseops.evals.aggregate import compute_globals
from leaseops.evals.report import print_summary, render_report
from leaseops.evals.run import run_cases
from leaseops.evals.schemas import GoldenItem

_EVALS_DIR = Path(__file__).resolve().parents[1] / "src/leaseops/evals"
_GOLDEN_PATH = _EVALS_DIR / "data/golden.json"
_REPORT_PATH = _EVALS_DIR / "reports/report.md"

_GoldenItems = TypeAdapter(list[GoldenItem])


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run evals against golden dataset.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Pick N random golden items instead of running all.",
    )
    args = parser.parse_args()

    with _GOLDEN_PATH.open() as f:
        items = _GoldenItems.validate_python(json.load(f))

    if args.limit is not None:
        random.shuffle(items)
        items = items[: args.limit]

    print(f"Running evals on {len(items)} item(s)...")
    results = await run_cases(items)
    g = compute_globals(results)
    report = render_report(results, g, datetime.now(UTC))

    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\nReport written to {_REPORT_PATH}")
    print()
    print_summary(g)


if __name__ == "__main__":
    asyncio.run(main())
