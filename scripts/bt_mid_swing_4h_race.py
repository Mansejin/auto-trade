#!/usr/bin/env python3
"""Race mid-swing-4h-ema-adx-v1 vs always bull-v2 vs B&H on Policy C windows."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.bt_policyC_continuous_equity import parse_perf  # noqa: E402
from scripts.bt_btc_cash_5050_rebalance import fetch_days, mdd, parse_d  # noqa: E402
from scripts.toolkit_bt import run_backtest  # noqa: E402

OUT = ROOT / "reports"
CACHE = ROOT / "reports/five-year/segment-csv-cache-midswing"
STRATS = {
    "mid_swing_v1": "strategies/mid-swing-4h-ema-adx-v1.json",
    "always_bull_v2": "strategies/regime-bull-trend-4h-v2.json",
}
WINDOWS = {
    "in_sample_5y": (date(2021, 7, 27), date(2026, 7, 26)),
    "oos_presample": (date(2018, 4, 12), date(2021, 7, 24)),
}


def run_bt(strat: str, start: str, end: str) -> Path:
    return run_backtest(strat, start, end, cache_dir=CACHE)


def bh_stats(start: date, end: date, by: dict) -> dict:
    days = [(d, px) for d, px in sorted(by.items()) if start <= d <= end]
    if len(days) < 2:
        return {}
    series = [px / days[0][1] for _, px in days]
    return {
        "return_pct": round((days[-1][1] / days[0][1] - 1) * 100, 2),
        "mdd_pct": round(mdd(series) * 100, 2),
    }


def main() -> None:
    print("fetch BH…", flush=True)
    raw = fetch_days("KRW-BTC", want=3500)
    by = {parse_d(c["candle_date_time_utc"]): float(c["trade_price"]) for c in raw}
    windows_out = {}
    for wname, (w0, w1) in WINDOWS.items():
        print(f"\n=== {wname} {w0}→{w1} ===", flush=True)
        row = {"start": w0.isoformat(), "end": w1.isoformat(), "bh": bh_stats(w0, w1, by)}
        for name, path in STRATS.items():
            print(f"  BT {name}…", flush=True)
            try:
                csv_path = run_bt(path, w0.isoformat(), w1.isoformat())
                perf = parse_perf(csv_path)
                ret = float(str(perf.get("total_return_pct", "0")).replace("+", ""))
                # toolkit MDD if present
                mdd_s = perf.get("max_drawdown_pct") or perf.get("mdd_pct") or perf.get("max_drawdown")
                try:
                    mdd_v = float(str(mdd_s).replace("%", "").replace("+", ""))
                except (TypeError, ValueError):
                    mdd_v = None
                n = perf.get("total_trades") or perf.get("trades")
                row[name] = {
                    "return_pct": ret,
                    "mdd_pct": mdd_v,
                    "trades": n,
                    "csv": str(csv_path.name),
                    "perf_keys": list(perf.keys())[:20],
                }
                print(f"    ret={ret}% mdd={mdd_v} trades={n}", flush=True)
            except Exception as ex:
                row[name] = {"error": str(ex)}
                print(f"    FAIL {ex}", flush=True)
        mid = row.get("mid_swing_v1", {})
        bh = row.get("bh", {})
        bull = row.get("always_bull_v2", {})
        if "return_pct" in mid and "return_pct" in bh:
            row["verdict"] = {
                "beats_bh_return": mid["return_pct"] > bh["return_pct"],
                "beats_bull_v2_return": mid.get("return_pct", -1e9)
                > bull.get("return_pct", 1e9)
                if "return_pct" in bull
                else None,
            }
        windows_out[wname] = row

    # overall: survive if both windows beat BH return (MDD secondary)
    ok = all(
        windows_out[w].get("verdict", {}).get("beats_bh_return") for w in WINDOWS
    )
    summary = {
        "card": "mid-swing-4h-ema-adx-v1",
        "note": "Shorter swing than Policy C map; no daily regime. Compare vs hold + always bull-v2.",
        "windows": windows_out,
        "verdict": "SURVIVES_VS_HOLD" if ok else "FALSIFIED_VS_HOLD",
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = OUT / f"bt-mid-swing-4h-race-{stamp}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
