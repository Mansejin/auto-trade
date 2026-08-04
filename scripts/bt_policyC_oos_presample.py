#!/usr/bin/env python3
"""Policy C OOS: pre-sample BEFORE 2021-07..2026-07 selection window.

Frozen LIVE map. No ADX/map retune. Compounds segment toolkit BTs vs B&H.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.regime_engine_v2 import build_segments, fetch_days  # noqa: E402
import scripts.bt_policyC_continuous_equity as pc  # noqa: E402
from scripts.bt_policyC_continuous_equity import (  # noqa: E402
    mdd,
    parse_perf,
    parse_trades,
    run_segment_bt,
    segment_daily_equity_v2,
)
from scripts.bt_btc_cash_5050_rebalance import fetch_days as fetch_bh_days, parse_d  # noqa: E402

OUT = ROOT / "reports"
CACHE = ROOT / "reports/five-year/segment-csv-cache-oos"
OOS_START = date(2017, 9, 1)
OOS_END = date(2021, 7, 26)
MAP_FILES = {
    "bull": "strategies/regime-bull-trend-4h-v2.json",
    "transition": "strategies/regime-bull-trend-4h-v2.json",
    "bear": "strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "strategies/regime-sideways-mr-4h-v5.json",
}


def main() -> None:
    print("fetching daily candles…", flush=True)
    candles = fetch_days(want=3500)
    print(
        f"candles={len(candles)} "
        f"{candles[0]['candle_date_time_utc'][:10]} → {candles[-1]['candle_date_time_utc'][:10]}",
        flush=True,
    )

    segs, _ = build_segments(candles)
    oos: list[dict] = []
    for s in segs:
        a, b = parse_d(s["start"]), parse_d(s["end"])
        if b < OOS_START or a > OOS_END:
            continue
        start, end = max(a, OOS_START), min(b, OOS_END)
        if (end - start).days < 5:
            continue
        regime = s["regime"]
        if regime not in MAP_FILES:
            continue
        oos.append(
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "regime": regime,
                "file": MAP_FILES[regime],
                "days": (end - start).days + 1,
            }
        )
    print(f"OOS segments={len(oos)}", flush=True)

    CACHE.mkdir(parents=True, exist_ok=True)
    pc.CACHE = CACHE

    days_bh_raw = fetch_bh_days(want=3500)
    bh_by = {
        parse_d(c["candle_date_time_utc"]): float(c["trade_price"])
        for c in days_bh_raw
    }
    days_bh = sorted(bh_by.items())

    eq = 1.0
    path_eq: list[tuple[date, float]] = []
    seg_reports: list[dict] = []

    for i, seg in enumerate(oos):
        s, e = seg["start"], seg["end"]
        print(f"[{i+1}/{len(oos)}] {seg['regime']} {s}→{e} {Path(seg['file']).stem}", flush=True)
        try:
            csv_path = run_segment_bt(seg["file"], s, e)
        except Exception as ex:
            print(f"  BT FAIL: {ex}", flush=True)
            seg_reports.append({**seg, "error": str(ex)})
            continue

        trades = parse_trades(csv_path)
        perf = parse_perf(csv_path)
        try:
            toolkit_ret = float(str(perf.get("total_return_pct", "0")).replace("+", "")) / 100.0
        except ValueError:
            toolkit_ret = 0.0
        expected_mult = 1.0 + toolkit_ret

        day_list: list[tuple[date, float]] = []
        cur = parse_d(s)
        end_d = parse_d(e)
        while cur <= end_d:
            if cur in bh_by:
                day_list.append((cur, bh_by[cur]))
            cur += timedelta(days=1)
        if len(day_list) < 2:
            seg_reports.append({**seg, "error": "no days"})
            continue

        start_eq = eq
        piece = segment_daily_equity_v2(trades, day_list, start_eq, expected_mult)
        if not piece:
            seg_reports.append({**seg, "error": "empty equity"})
            continue
        if path_eq and piece and piece[0][0] == path_eq[-1][0]:
            piece = piece[1:]
        eq = piece[-1][1]
        path_eq.extend(piece)
        seg_ret = eq / start_eq - 1.0
        bh_ret = day_list[-1][1] / day_list[0][1] - 1.0
        seg_reports.append(
            {
                **seg,
                "strat_ret_pct": round(seg_ret * 100, 2),
                "bh_ret_pct": round(bh_ret * 100, 2),
                "toolkit_ret_pct": round(toolkit_ret * 100, 2),
                "end_eq": round(eq, 4),
                "n_trades": len(trades),
            }
        )
        print(
            f"  strat={seg_ret*100:+.2f}% toolkit={toolkit_ret*100:+.2f}% "
            f"bh={bh_ret*100:+.2f}% eq={eq:.3f}",
            flush=True,
        )

    if not path_eq:
        raise SystemExit("no equity path")

    bh_start = next(px for d, px in days_bh if d >= OOS_START)
    bh_end = next(px for d, px in reversed(days_bh) if d <= OOS_END)
    bh_mult = bh_end / bh_start
    s0 = path_eq[0][1]
    series_n = [e / s0 for _, e in path_eq]
    pc_mult = series_n[-1]
    pc_mdd = mdd(series_n)
    bh_series = [px / bh_start for d, px in days_bh if OOS_START <= d <= OOS_END]
    bh_mdd = mdd(bh_series) if bh_series else None

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    summary = {
        "window": {"start": OOS_START.isoformat(), "end": OOS_END.isoformat()},
        "note": "OOS before 5y Policy C selection sample. Map frozen — no retune.",
        "map": MAP_FILES,
        "n_segments": len(oos),
        "n_segments_ok": sum(1 for x in seg_reports if "error" not in x),
        "policyC_multiple": round(pc_mult, 4),
        "policyC_return_pct": round((pc_mult - 1) * 100, 2),
        "policyC_mdd_pct": round(pc_mdd * 100, 2) if pc_mdd is not None else None,
        "bh_multiple": round(bh_mult, 4),
        "bh_return_pct": round((bh_mult - 1) * 100, 2),
        "bh_mdd_pct": round(bh_mdd * 100, 2) if bh_mdd is not None else None,
        "beats_bh_return": bool(pc_mult > bh_mult),
        "segments": seg_reports,
    }
    out = OUT / f"bt-policyC-oos-presample-{stamp}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k != "segments"}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
