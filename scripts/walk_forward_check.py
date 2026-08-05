#!/usr/bin/env python3
"""Simple walk-forward checker for ACTIVE / candidate strategies.

Splits a long window into train/test folds (sequential, no purge CV).
Prints toolkit metrics per fold. Does not auto-promote.

Example:
  python3 scripts/walk_forward_check.py \
    --strategy strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json \
    --start 2021-07-27 --end 2026-07-26 --fold-months 12
"""
from __future__ import annotations

import argparse
import json
import sys
from calendar import monthrange
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_backtest  # noqa: E402


def add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, monthrange(y, m)[1])
    return date(y, m, day)


def parse_d(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _f(raw: dict[str, str], key: str) -> float | None:
    v = raw.get(key)
    if v is None or v.startswith("N/A"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def run_bt(strategy: Path, start: str, end: str) -> dict:
    csv_path = run_backtest(strategy, start, end)
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    in_perf = False
    raw: dict[str, str] = {}
    for line in lines:
        if line.startswith("# section: performance"):
            in_perf = True
            continue
        if in_perf and line.startswith("# section:"):
            break
        if not in_perf or line.startswith("metric") or not line.strip():
            continue
        k, v = line.split(",", 1)
        raw[k] = v
    out: dict = {
        "ret": _f(raw, "total_return_pct"),
        "bh": _f(raw, "benchmark_pct"),
        "cagr": _f(raw, "cagr_pct"),
        "mdd": _f(raw, "mdd_pct"),
        "n": int(_f(raw, "trades") or 0),
        "pf": _f(raw, "profit_factor_before_fees"),
    }
    out["ok"] = out["ret"] is not None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--fold-months", type=int, default=12)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    strat = Path(args.strategy)
    if not strat.is_absolute():
        strat = ROOT / strat
    start = parse_d(args.start)
    end = parse_d(args.end)
    folds = []
    cur = start
    i = 1
    while cur < end:
        nxt = min(add_months(cur, args.fold_months), end)
        if nxt <= cur:
            break
        # fold end is inclusive date for toolkit --end; use nxt as exclusive-ish by keeping nxt
        fold_end = nxt if nxt < end else end
        label = f"F{i}"
        print(f"=== {label} {cur} .. {fold_end} ===", flush=True)
        m = run_bt(strat, cur.isoformat(), fold_end.isoformat())
        print(m, flush=True)
        folds.append({"fold": label, "start": cur.isoformat(), "end": fold_end.isoformat(), **m})
        cur = fold_end if fold_end > cur else add_months(cur, 1)
        # advance to next day to avoid overlap if end==start of next
        if cur < end:
            from datetime import timedelta
            if folds and folds[-1]["end"] == cur.isoformat():
                cur = cur + timedelta(days=1)
        i += 1

    pos = sum(1 for f in folds if f.get("ret") is not None and f["ret"] > 0)
    report = {
        "strategy": str(strat.relative_to(ROOT)),
        "start": args.start,
        "end": args.end,
        "fold_months": args.fold_months,
        "folds": folds,
        "positive_folds": pos,
        "n_folds": len(folds),
        "note": "Walk-forward diagnostic only. Not a LIVE promotion signal.",
    }
    out = Path(args.out) if args.out else ROOT / "reports" / "improve" / f"walkforward-{strat.stem}.json"
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print("wrote", out)
    print(f"positive folds {pos}/{len(folds)}")


if __name__ == "__main__":
    main()
