"""Run the evals pipeline against the golden dataset.

Usage:
    uv run python scripts/run_evals.py
    uv run python scripts/run_evals.py --limit 3
    uv run python scripts/run_evals.py --ids a,b,c
    uv run python scripts/run_evals.py --failures
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
from datetime import UTC, datetime
from pathlib import Path

from pydantic import TypeAdapter
from seed import seed

from leaseops.core.config import settings
from leaseops.db.session import open_session, use_database
from leaseops.evals.aggregate import compute_globals
from leaseops.evals.report import render_report
from leaseops.evals.run import run_cases
from leaseops.evals.schemas import GoldenItem

_EVALS_DIR = Path(__file__).resolve().parents[1] / "src/leaseops/evals"
_GOLDEN_PATH = _EVALS_DIR / "data/golden.json"
_REPORTS_DIR = _EVALS_DIR / "reports"

_FAILURE_CASE_IDS = [
    "kevin-chen-fridge-not-cooling",
    "priya-nadkarni-dishwasher-dead",
    "carlos-morales-storm-fence",
    "carlos-morales-trampoline",
    "maria-vega-cat-approval",
    "kevin-chen-paint-bedroom",
    "isabel-reyes-cousin-moving-in",
]

_GoldenItems = TypeAdapter(list[GoldenItem])
_SPINNER_FRAMES = "⠋⠙⠹⠼⠴⠦⠧⠇⠏"


def _parse_ids(raw: str) -> list[str]:
    ids = [part.strip() for part in raw.split(",") if part.strip()]
    if not ids:
        raise argparse.ArgumentTypeError("expected at least one item id")
    return ids


def _select_by_ids(
    items: list[GoldenItem],
    ids: list[str],
    *,
    parser: argparse.ArgumentParser,
) -> list[GoldenItem]:
    by_id = {item.id: item for item in items}
    missing = [item_id for item_id in ids if item_id not in by_id]
    if missing:
        parser.error(f"unknown item id(s): {', '.join(missing)}")
    return [by_id[item_id] for item_id in ids]


class _Progress:
    def __init__(self) -> None:
        self._label = ""
        self._stop: asyncio.Event | None = None
        self._task: asyncio.Task[None] | None = None

    async def start(self, i: int, n: int, item: GoldenItem) -> None:
        await self._stop_spinner()
        self._label = f"[{i}/{n}] {item.id}"
        self._stop = asyncio.Event()
        self._task = asyncio.create_task(self._spin())

    async def done(self, i: int, n: int, item: GoldenItem) -> None:
        await self._stop_spinner()
        print(f"✓ [{i}/{n}] {item.id}")

    async def error(self, i: int, n: int, item: GoldenItem, exc: Exception) -> None:
        await self._stop_spinner()
        print(f"✗ [{i}/{n}] {item.id} — skipped: {exc}")

    async def _spin(self) -> None:
        assert self._stop is not None
        frame = 0
        while not self._stop.is_set():
            print(
                f"\r{_SPINNER_FRAMES[frame % len(_SPINNER_FRAMES)]} {self._label}",
                end="",
                flush=True,
            )
            frame += 1
            await asyncio.sleep(0.08)

    async def _stop_spinner(self) -> None:
        if self._task is None or self._stop is None:
            return
        self._stop.set()
        await self._task
        self._task = None
        self._stop = None
        print(f"\r{' ' * (len(self._label) + 4)}\r", end="", flush=True)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run evals against golden dataset.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Pick N random golden items instead of running all.",
    )
    parser.add_argument(
        "--ids",
        type=_parse_ids,
        default=None,
        metavar="ID,...",
        help="Comma-separated golden item ids to run only.",
    )
    parser.add_argument(
        "--failures",
        action="store_true",
        help="Run only the hardcoded responsibility failure cases.",
    )
    args = parser.parse_args()

    if args.ids is not None and args.failures:
        parser.error("--ids and --failures are mutually exclusive")

    with _GOLDEN_PATH.open() as f:
        items = _GoldenItems.validate_python(json.load(f))

    if args.failures:
        items = _select_by_ids(items, _FAILURE_CASE_IDS, parser=parser)
    elif args.ids is not None:
        items = _select_by_ids(items, args.ids, parser=parser)

    if args.limit is not None:
        random.shuffle(items)
        items = items[: args.limit]

    print("🌱 Truncating and seeding evals database...")
    async with use_database(settings.evals_database_url), open_session() as session:
        n_tenants = await seed(session)
    print(f"Seeded {n_tenants} tenant(s)")

    print(f"🧪 Running evals on {len(items)} item(s)...")
    progress = _Progress()
    results = await run_cases(
        items,
        on_start=progress.start,
        on_done=progress.done,
        on_error=progress.error,
    )
    skipped = len(items) - len(results)
    g = compute_globals(results)
    generated_at = datetime.now(UTC)
    report = render_report(results, g, generated_at)

    report_path = _REPORTS_DIR / generated_at.strftime("eval-%Y%m%d-%H%M%S.md")
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    if skipped:
        print(
            f"\nDone. ⚠️  Report written to {report_path.name} "
            f"({skipped} case(s) skipped due to errors)"
        )
    else:
        print(f"\nDone. ✅ Report written to {report_path.name}")


if __name__ == "__main__":
    asyncio.run(main())
