from __future__ import annotations

import json
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent.parent / "seed_data"


def load_json(name: str) -> list[dict[str, object]]:
    path = SEED_DIR / name
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise TypeError(f"{name} must be a JSON array")
    return data


def main() -> None:
    tenants = load_json("tenants.json")
    emails = load_json("emails.json")

    print(f"Loaded {len(tenants)} tenant(s) and {len(emails)} email(s) from {SEED_DIR}")
    print("(no DB tables yet — load only)")


if __name__ == "__main__":
    main()
