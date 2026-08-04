"""Fetch Bitget QQQUSDT 4H candles for manual channel sampling."""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://api.bitget.com/api/v3/market/history-candles"
SYMBOL = "QQQUSDT"
INTERVAL = "4H"
LIMIT = 100


def fetch_page(end_ms: int) -> list:
    url = (
        f"{BASE}?category=USDT-FUTURES&symbol={SYMBOL}"
        f"&interval={INTERVAL}&limit={LIMIT}&endTime={end_ms}&type=market"
    )
    with urllib.request.urlopen(url, timeout=30) as r:
        payload = json.load(r)
    if str(payload.get("code")) not in ("00000", "0") and payload.get("data") is None:
        raise RuntimeError(payload)
    return payload.get("data") or []


def main() -> None:
    end = int(datetime(2026, 7, 29, 12, tzinfo=timezone.utc).timestamp() * 1000)
    start_floor = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp() * 1000)
    all_rows: dict[int, list] = {}
    for page in range(12):
        data = fetch_page(end)
        if not data:
            print("empty page", page)
            break
        for row in data:
            all_rows[int(row[0])] = row
        oldest = min(int(x[0]) for x in data)
        newest = max(int(x[0]) for x in data)
        print(
            f"page {page}: n={len(data)} "
            f"{datetime.fromtimestamp(oldest / 1000, tz=timezone.utc)} -> "
            f"{datetime.fromtimestamp(newest / 1000, tz=timezone.utc)}"
        )
        if oldest <= start_floor:
            break
        end = oldest - 1
        time.sleep(0.2)

    rows = [all_rows[k] for k in sorted(all_rows)]
    out = Path(__file__).with_name("data") / "qqq_usdt_4h.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows), encoding="utf-8")
    print("saved", len(rows), "bars ->", out)
    if rows:
        print(
            "range",
            datetime.fromtimestamp(int(rows[0][0]) / 1000, tz=timezone.utc),
            "->",
            datetime.fromtimestamp(int(rows[-1][0]) / 1000, tz=timezone.utc),
        )


if __name__ == "__main__":
    main()
