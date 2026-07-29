#!/usr/bin/env python3
"""AE12 event-study stub — runs only when enough forward data exists.

Pre-registered hypotheses (do not change after collection starts):
  H1: OKX fundingRate <= -0.0002 → next UTC day KRW-BTC ret mean > baseline
  H2: |Upbit orderbook imbalance| >= 0.4 → next 1h abs return > baseline abs mean
     (direction = sign of imbalance)

Holdout: last 30% of collection calendar span by time (frozen rule).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECT = ROOT / "reports" / "ae12-collect"
FUNDING = COLLECT / "okx-funding.jsonl"
MIN_FUNDING_ROWS = 24 * 30  # ~monthly hourly; adjust if cron differs
OUT = COLLECT / "event-study-status.json"


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.open())


def main() -> int:
    n = count_lines(FUNDING)
    status = {
        "ready": n >= MIN_FUNDING_ROWS,
        "funding_rows": n,
        "min_funding_rows": MIN_FUNDING_ROWS,
        "message": (
            "enough rows — implement/run study next"
            if n >= MIN_FUNDING_ROWS
            else "keep collecting; do not mine thresholds yet"
        ),
        "hypotheses_frozen": [
            "H1 fundingRate<=-0.0002 → next-day KRW-BTC mean > baseline",
            "H2 |imbalance|>=0.4 → next 1h |ret| > baseline (dir=sign)",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
