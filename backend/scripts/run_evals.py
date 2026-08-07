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
from leaseops.evals.report import render_report
from leaseops.evals.run import run_cases
from leaseops.evals.schemas import GoldenItem

_EVALS_DIR = Path(__file__).resolve().parents[1] / "src/leaseops/evals"
_GOLDEN_PATH = _EVALS_DIR / "data/golden.json"
_REPORTS_DIR = _EVALS_DIR / "reports"

_GoldenItems = TypeAdapter(list[GoldenItem])
_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


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
    args = parser.parse_args()

    with _GOLDEN_PATH.open() as f:
        items = _GoldenItems.validate_python(json.load(f))

    if args.limit is not None:
        random.shuffle(items)
        items = items[: args.limit]

    print(f"Running evals on {len(items)} item(s)...")
    progress = _Progress()
    results = await run_cases(items, on_start=progress.start, on_done=progress.done)
    g = compute_globals(results)
    generated_at = datetime.now(UTC)
    report = render_report(results, g, generated_at)

    report_path = _REPORTS_DIR / generated_at.strftime("eval-%H%M%S-%Y%m%d.md")
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"\nDone. Report written to {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
