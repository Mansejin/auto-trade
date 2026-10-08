"""Shared helpers for T-005 card backtests (stdlib only). Data: data/research/*.csv (see docs/research/data-catalog.md)."""
from __future__ import annotations

import csv
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
OUT = ROOT / "reports" / "research-cards"
N_RANDOM = 1000
SEED = 20261008


def rows(name: str):
    with open(DATA / f"{name}.csv", encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f)


def d(s: str) -> date:
    return date.fromisoformat(s[:10])


def daily_bars(name: str, key: str = "symbol", only: set | None = None) -> dict:
    """{symbol: {date: (open, close, quote_volume)}}"""
    out: dict = {}
    for r in rows(name):
        k = r[key]
        if only is not None and k not in only:
            continue
        qv = r.get("quote_volume") or r.get("value_krw") or 0
        out.setdefault(k, {})[d(r["date_utc"])] = (float(r["open"]), float(r["close"]), float(qv))
    return out


def pf(rets) -> float | None:
    g = sum(x for x in rets if x > 0)
    l = -sum(x for x in rets if x < 0)
    return round(g / l, 3) if l > 0 else (None if g == 0 else float("inf"))


def summarize(rets: list[float]) -> dict:
    """Sequential compounding of non-overlapping trade/period returns."""
    if not rets:
        return {"n": 0}
    eq = peak = 1.0
    mdd = 0.0
    for r in rets:
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    return {
        "n": len(rets),
        "pf": pf(rets),
        "ret_pct": round((eq - 1) * 100, 2),
        "mean_pct": round(sum(rets) / len(rets) * 100, 3),
        "win_pct": round(sum(r > 0 for r in rets) / len(rets) * 100, 1),
        "mdd_pct": round(mdd * 100, 2),
    }


def sharpe(rets: list[float], per_year: float) -> float | None:
    if len(rets) < 2:
        return None
    m = sum(rets) / len(rets)
    sd = math.sqrt(sum((x - m) ** 2 for x in rets) / (len(rets) - 1))
    return round(m / sd * math.sqrt(per_year), 2) if sd else None


def pct_rank(value: float, dist: list[float]) -> float:
    """Share of random runs strictly below value (0..100). >=95 means top 5%."""
    return round(sum(x < value for x in dist) / len(dist) * 100, 1)


def halves(items: list, key) -> tuple[list, list]:
    """Split items (sorted by key) at the midpoint date of their key range."""
    if not items:
        return [], []
    ks = [key(x) for x in items]
    mid = ks[0] + (ks[-1] - ks[0]) / 2
    return [x for x in items if key(x) <= mid], [x for x in items if key(x) > mid]


def rng() -> random.Random:
    return random.Random(SEED)


def daterange(a: date, b: date):
    while a <= b:
        yield a
        a += timedelta(days=1)


def write_json(slug: str, obj: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{slug}.json"
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return p
