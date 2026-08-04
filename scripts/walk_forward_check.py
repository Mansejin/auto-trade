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
import subprocess
from calendar import monthrange
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TK = ROOT / ".agents" / "skills" / "backtest" / "scripts" / "upbit-strategy-toolkit.sh"


def add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, monthrange(y, m)[1])
    return date(y, m, day)


def parse_d(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def run_bt(strategy: Path, start: str, end: str) -> dict:
    p = subprocess.run(
        ["bash", str(TK), "backtest", "run", str(strategy), "--start", start, "--end", end],
        capture_output=True,
        text=True,
    )
    text = (p.stdout or "") + "\n" + (p.stderr or "")
    out = {}
    for line in text.splitlines():
        t = line.strip()
        if t.startswith("Total Return"):
            out["ret"] = float(t.split()[2].replace("%", "").replace("+", ""))
        elif t.startswith("Benchmark"):
            out["bh"] = float(t.split()[1].replace("%", "").replace("+", ""))
        elif t.startswith("CAGR"):
            out["cagr"] = float(t.split()[1].replace("%", "").replace("+", ""))
        elif t.startswith("MDD"):
            out["mdd"] = float(t.split()[1].replace("%", "").replace("+", ""))
        elif t.startswith("Trades"):
            out["n"] = int(t.split()[1])
        elif t.startswith("Profit Factor"):
            raw = t.split()[2]
            out["pf"] = None if raw in ("∞", "N/A") else float(raw)
    out["ok"] = "ret" in out
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
