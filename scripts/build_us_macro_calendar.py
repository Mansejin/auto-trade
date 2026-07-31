#!/usr/bin/env python3
"""Build frozen US macro calendar JSON (FOMC / CPI / NFP) 2021–2026.

NFP = first Friday each month 08:30 America/New_York.
CPI = mid-month release dates (frozen list; BLS schedule).
FOMC = Fed decision days 14:00 America/New_York (frozen list).
"""
from __future__ import annotations

import json
from calendar import monthcalendar
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config" / "us-macro-calendar.json"
NY = ZoneInfo("America/New_York")

# Fed FOMC announcement days (decision day)
FOMC_DAYS = [
    # 2021
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16",
    "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
    # 2022
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15",
    "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    # 2023
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14",
    "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    # 2024
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
    "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    # 2025
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
    "2025-07-30", "2025-09-17", "2025-11-05", "2025-12-17",
    # 2026
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
    "2026-07-29",
]

# BLS CPI release dates (2021–mid 2026) — frozen snapshot
CPI_DAYS = [
    "2021-01-13", "2021-02-10", "2021-03-10", "2021-04-13", "2021-05-12", "2021-06-10",
    "2021-07-13", "2021-08-11", "2021-09-14", "2021-10-13", "2021-11-10", "2021-12-10",
    "2022-01-12", "2022-02-10", "2022-03-10", "2022-04-12", "2022-05-11", "2022-06-10",
    "2022-07-13", "2022-08-10", "2022-09-13", "2022-10-13", "2022-11-10", "2022-12-13",
    "2023-01-12", "2023-02-14", "2023-03-14", "2023-04-12", "2023-05-10", "2023-06-13",
    "2023-07-12", "2023-08-10", "2023-09-13", "2023-10-12", "2023-11-14", "2023-12-12",
    "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10", "2024-05-15", "2024-06-12",
    "2024-07-11", "2024-08-14", "2024-09-11", "2024-10-10", "2024-11-13", "2024-12-11",
    "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13", "2025-06-11",
    "2025-07-15", "2025-08-12", "2025-09-11", "2025-10-15", "2025-11-13", "2025-12-10",
    "2026-01-13", "2026-02-11", "2026-03-11", "2026-04-10", "2026-05-12", "2026-06-10",
    "2026-07-14",
]


def first_friday(year: int, month: int) -> date:
    for week in monthcalendar(year, month):
        if week[4]:  # Friday
            return date(year, month, week[4])
    raise RuntimeError(f"no Friday {year}-{month}")


def ny_to_utc(d: date, hh: int, mm: int) -> str:
    local = datetime.combine(d, time(hh, mm), tzinfo=NY)
    return local.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    events: list[dict] = []
    for s in FOMC_DAYS:
        d = date.fromisoformat(s)
        events.append({"type": "FOMC", "ts_utc": ny_to_utc(d, 14, 0)})
    for s in CPI_DAYS:
        d = date.fromisoformat(s)
        events.append({"type": "CPI", "ts_utc": ny_to_utc(d, 8, 30)})
    for y in range(2021, 2027):
        for m in range(1, 13):
            if y == 2026 and m > 7:
                break
            d = first_friday(y, m)
            events.append({"type": "NFP", "ts_utc": ny_to_utc(d, 8, 30)})
    events.sort(key=lambda e: e["ts_utc"])
    # de-dupe same ts
    seen: set[str] = set()
    uniq = []
    for e in events:
        key = f"{e['type']}|{e['ts_utc']}"
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    payload = {
        "version": 1,
        "built_by": "scripts/build_us_macro_calendar.py",
        "tz_note": "America/New_York local → UTC",
        "n_events": len(uniq),
        "events": uniq,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} n={len(uniq)}")


if __name__ == "__main__":
    main()
