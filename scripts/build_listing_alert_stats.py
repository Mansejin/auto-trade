#!/usr/bin/env python3
"""Freeze historical distribution for the listing alert (alerts/listing_alert.py) -> config/listing-alert-stats.json

  python scripts/build_listing_alert_stats.py

Events = OOS events of reports/research-cards/upbit-listing-fade.json (listing >= 2023-07-01).
Per event, Binance perp daily bars: ret7 = open(D+8)/open(D+1)-1 (price only, no funding/costs),
high7 = max high D+1..D+7 / open(D+1) - 1, perp age = D - first perp bar. Run once offline; no live re-fit.
"""
from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path

from bt_cards_common import DATA, d

ROOT = Path(__file__).resolve().parents[1]
OOS0 = date(2023, 7, 1)
BUCKETS = ((0, 30, "<=30d"), (31, 180, "31-180d"), (181, 10**6, ">180d"))


def q(v: list[float], p: float) -> float:
    s = sorted(v)
    return s[min(len(s) - 1, int(p * len(s)))]


def main():
    ev = [e for e in json.loads((ROOT / "reports/research-cards/upbit-listing-fade.json").read_text(encoding="utf-8"))["events"]
          if d(e["listing"]) >= OOS0]
    syms = {e["sym"] for e in ev}
    bars: dict = {}
    with open(DATA / "binance_perp_listing_1d.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["symbol"] in syms:
                bars.setdefault(r["symbol"], {})[d(r["date_utc"])] = (float(r["open"]), float(r["high"]))
    rets, highs, ages = [], [], []
    for e in ev:
        b, e0 = bars[e["sym"]], d(e["entry"])
        p0 = b[e0][0]
        rets.append(b[e0 + timedelta(7)][0] / p0 - 1)
        highs.append(max(b[e0 + timedelta(i)][1] for i in range(7) if e0 + timedelta(i) in b) / p0 - 1)
        ages.append((d(e["listing"]) - min(b)).days)
    out = {
        "source": "reports/research-cards/upbit-listing-fade.json OOS events, Binance USDT-M perp daily, entry open D+1 UTC",
        "period": f"{min(e['listing'] for e in ev)}..{max(e['listing'] for e in ev)}",
        "n": len(ev),
        "ret7_p10_pct": round(q(rets, 0.10) * 100, 1),
        "ret7_p50_pct": round(q(rets, 0.50) * 100, 1),
        "ret7_p90_pct": round(q(rets, 0.90) * 100, 1),
        "high7_ge30_n": sum(h >= 0.30 for h in highs),
        "high7_ge30_pct": round(sum(h >= 0.30 for h in highs) / len(ev) * 100, 1),
        "high7_max_pct": round(max(highs) * 100, 1),
        "age_buckets": {lab: {"n": len(r := [x for x, a in zip(rets, ages) if lo <= a <= hi]),
                              "ret7_p50_pct": round(q(r, 0.5) * 100, 1) if r else None}
                        for lo, hi, lab in BUCKETS},
    }
    p = ROOT / "config" / "listing-alert-stats.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
