#!/usr/bin/env python3
"""Monthly LIVE review for Policy C / Williams sideways (no auto-deploy).

Reads local/VPS logs under AUTO_TRADE_ROOT:
  - logs/regime-switch.jsonl
  - logs/regime-current.json
  - logs/premium-watcher.jsonl (optional)

Writes:
  reports/improve/YYYYMM-live-month-review.md
  reports/review-state/live-month-review-latest.json

Improvement rules (frozen — do not retune indicator thresholds from one month):
  - If Williams mount-days < 7: INCONCLUSIVE (sample)
  - If sideways_gate williams days had bot still on other slug: OPS_DRIFT
  - Suggest only: keep | demote_sideways_to_v5 | raise_dwell_to_14 | lower_dwell_to_7
  - Never auto-change POLICY / never auto-deploy

Cron example (1st of month 16:00 UTC):
  0 16 1 * * cd ~/auto-trade && python3 scripts/monthly_live_review.py >> logs/monthly-review.cron.log 2>&1
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("AUTO_TRADE_ROOT", str(Path(__file__).resolve().parents[1])))
REGIME_LOG = ROOT / "logs" / "regime-switch.jsonl"
PREMIUM_LOG = ROOT / "logs" / "premium-watcher.jsonl"
REGIME_CURRENT = ROOT / "logs" / "regime-current.json"
OUT_DIR = ROOT / "reports" / "improve"
STATE_OUT = ROOT / "reports" / "review-state" / "live-month-review-latest.json"

WILLIAMS = "regime-sideways-mr-1h-williams-v1.json"
FALLBACK = "regime-sideways-mr-4h-v5.json"


def _parse_ts(rec: dict) -> datetime | None:
    if rec.get("ts_epoch"):
        return datetime.fromtimestamp(int(rec["ts_epoch"]), tz=timezone.utc)
    ts = rec.get("ts_utc") or rec.get("updated_at")
    if not ts:
        return None
    try:
        return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def month_bounds(ym: str) -> tuple[datetime, datetime]:
    y, m = map(int, ym.split("-"))
    start = datetime(y, m, 1, tzinfo=timezone.utc)
    if m == 12:
        end = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(y, m + 1, 1, tzinfo=timezone.utc)
    return start, end


def in_month(dt: datetime | None, start: datetime, end: datetime) -> bool:
    return dt is not None and start <= dt < end


def analyze(ym: str) -> dict:
    start, end = month_bounds(ym)
    regime_rows = [r for r in load_jsonl(REGIME_LOG) if in_month(_parse_ts(r), start, end)]
    premium_rows = [r for r in load_jsonl(PREMIUM_LOG) if in_month(_parse_ts(r), start, end)]

    actions = Counter(r.get("action") for r in regime_rows)
    regimes = Counter(r.get("regime") for r in regime_rows)
    to_williams = 0
    to_fallback = 0
    switches = 0
    for r in regime_rows:
        if r.get("action") == "switched":
            switches += 1
            new = r.get("new") or ""
            if WILLIAMS in new:
                to_williams += 1
            if FALLBACK in new:
                to_fallback += 1

    current = {}
    if REGIME_CURRENT.exists():
        try:
            current = json.loads(REGIME_CURRENT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            current = {}

    # Decision (ops-level only)
    suggestion = "keep"
    reason = "Insufficient evidence to change Policy C map"
    if to_williams == 0 and regimes.get("sideways", 0) >= 5:
        suggestion = "ops_check"
        reason = "Sideways labels seen but zero switches onto Williams — check dwell gate / dwell cron"
    elif to_williams >= 3 and actions.get("position_skip", 0) > to_williams:
        suggestion = "ops_check"
        reason = "Williams targeted but often blocked by open position — review flatten/dwell ops"
    # demote only if human later fills live PnL fields; placeholder gate
    live_pnl = os.environ.get("MONTHLY_LIVE_PNL_PCT")
    live_trades = os.environ.get("MONTHLY_LIVE_TRADES")
    if live_pnl is not None and live_trades is not None:
        try:
            pnl = float(live_pnl)
            n = int(live_trades)
            if n >= 8 and pnl < -5.0:
                suggestion = "demote_sideways_to_v5"
                reason = f"Human-supplied month PnL {pnl}% on {n} trades < -5% — consider demote"
            elif n >= 8 and pnl >= 0:
                suggestion = "keep"
                reason = f"Human-supplied month PnL {pnl}% on {n} trades — keep"
            elif n < 8:
                suggestion = "inconclusive"
                reason = f"Only {n} trades — wait another month (no threshold retune)"
        except ValueError:
            pass

    return {
        "ok": True,
        "month": ym,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy": current.get("policy"),
        "regime_current": {
            "regime": current.get("regime"),
            "selected_file": current.get("selected_file"),
            "sideways_dwell": current.get("sideways_dwell"),
            "sideways_gate": current.get("sideways_gate"),
        },
        "regime_log": {
            "rows": len(regime_rows),
            "actions": dict(actions),
            "regimes": dict(regimes),
            "switches": switches,
            "switches_to_williams": to_williams,
            "switches_to_fallback_v5": to_fallback,
        },
        "premium_log_rows": len(premium_rows),
        "suggestion": suggestion,
        "reason": reason,
        "allowed_improvements": [
            "keep",
            "demote_sideways_to_v5",
            "raise_dwell_to_14",
            "ops_check",
            "inconclusive",
        ],
        "forbidden": [
            "retune Williams WR/ADX thresholds from this month alone",
            "auto-deploy without human",
        ],
    }


def render_md(data: dict) -> str:
    rl = data["regime_log"]
    rc = data["regime_current"]
    return f"""# LIVE month review — {data['month']}

Generated: {data['generated_at']}  
Policy tag: `{data.get('policy')}`

## Current snapshot
- regime: `{rc.get('regime')}`
- selected: `{rc.get('selected_file')}`
- sideways_dwell / gate: `{rc.get('sideways_dwell')}` / `{rc.get('sideways_gate')}`

## Regime-switch log ({data['month']})
- rows: {rl['rows']}
- actions: `{json.dumps(rl['actions'], ensure_ascii=False)}`
- regimes: `{json.dumps(rl['regimes'], ensure_ascii=False)}`
- switches: {rl['switches']} (to Williams: {rl['switches_to_williams']}, to v5 fallback: {rl['switches_to_fallback_v5']})
- premium-watcher rows: {data['premium_log_rows']}

## Suggestion (ops only)
- **{data['suggestion']}** — {data['reason']}

## Rules
- Allowed: {', '.join(data['allowed_improvements'])}
- Forbidden: {'; '.join(data['forbidden'])}

## Human PnL input (optional next run)
```bash
MONTHLY_LIVE_PNL_PCT=-2.5 MONTHLY_LIVE_TRADES=10 python3 scripts/monthly_live_review.py --month {data['month']}
```

Do not auto-deploy from this report.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--month",
        help="YYYY-MM (default: previous UTC month)",
    )
    args = ap.parse_args()
    if args.month:
        ym = args.month
    else:
        now = datetime.now(timezone.utc)
        y, m = now.year, now.month - 1
        if m == 0:
            y, m = y - 1, 12
        ym = f"{y:04d}-{m:02d}"

    data = analyze(ym)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_OUT.parent.mkdir(parents=True, exist_ok=True)
    md_path = OUT_DIR / f"{ym.replace('-', '')}-live-month-review.md"
    md_path.write_text(render_md(data), encoding="utf-8")
    STATE_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "month": ym, "md": str(md_path), "suggestion": data["suggestion"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
