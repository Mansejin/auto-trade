#!/usr/bin/env python3
"""Fair race: Famous mount vs Policy C on the same regime segments.

Same classifier segments; only STRATEGY map differs. Compounds toolkit segment
returns (not frozen Policy C path rets). Windows: in-sample 5y + OOS presample.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
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
CACHE = ROOT / "reports/five-year/segment-csv-cache-famous-race"

POLICY_C = {
    "bull": "strategies/regime-bull-trend-4h-v2.json",
    "transition": "strategies/regime-bull-trend-4h-v2.json",
    "bear": "strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "strategies/regime-sideways-mr-4h-v5.json",
}
FAMOUS = {
    "bull": "strategies/famous-faber-10mo-sma-1d.json",
    "transition": "strategies/famous-faber-10mo-sma-1d.json",
    "bear": "strategies/famous-cash-flat-1d.json",
    "sideways": "strategies/famous-wilder-rsi-mr-1d.json",
}
WINDOWS = {
    "in_sample_5y": (date(2021, 7, 27), date(2026, 7, 26)),
    "oos_presample": (date(2018, 4, 12), date(2021, 7, 24)),
}


def clip_segs(segs: list[dict], start: date, end: date, fmap: dict[str, str]) -> list[dict]:
    out: list[dict] = []
    for s in segs:
        a, b = parse_d(s["start"]), parse_d(s["end"])
        if b < start or a > end:
            continue
        lo, hi = max(a, start), min(b, end)
        if (hi - lo).days < 5:
            continue
        regime = s["regime"]
        if regime not in fmap:
            continue
        out.append(
            {
                "start": lo.isoformat(),
                "end": hi.isoformat(),
                "regime": regime,
                "file": fmap[regime],
                "days": (hi - lo).days + 1,
            }
        )
    return out


def run_map(
    name: str,
    segs: list[dict],
    bh_by: dict[date, float],
    w_start: date,
    w_end: date,
) -> dict:
    eq = 1.0
    path_eq: list[tuple[date, float]] = []
    reports: list[dict] = []
    for i, seg in enumerate(segs):
        s, e = seg["start"], seg["end"]
        print(f"  [{name} {i+1}/{len(segs)}] {seg['regime']} {s}→{e} {Path(seg['file']).stem}", flush=True)
        try:
            csv_path = run_segment_bt(seg["file"], s, e)
            time.sleep(0.8)  # Upbit rate-limit cushion
        except Exception as ex:
            print(f"    FAIL {ex}", flush=True)
            reports.append({**seg, "error": str(ex)})
            continue
        trades = parse_trades(csv_path)
        perf = parse_perf(csv_path)
        try:
            toolkit_ret = float(str(perf.get("total_return_pct", "0")).replace("+", "")) / 100.0
        except ValueError:
            toolkit_ret = 0.0
        day_list: list[tuple[date, float]] = []
        cur = parse_d(s)
        end_d = parse_d(e)
        while cur <= end_d:
            if cur in bh_by:
                day_list.append((cur, bh_by[cur]))
            cur += timedelta(days=1)
        if len(day_list) < 2:
            reports.append({**seg, "error": "no days"})
            continue
        start_eq = eq
        piece = segment_daily_equity_v2(trades, day_list, start_eq, 1.0 + toolkit_ret)
        if not piece:
            reports.append({**seg, "error": "empty equity"})
            continue
        if path_eq and piece[0][0] == path_eq[-1][0]:
            piece = piece[1:]
        eq = piece[-1][1]
        path_eq.extend(piece)
        reports.append(
            {
                **seg,
                "toolkit_ret_pct": round(toolkit_ret * 100, 2),
                "strat_ret_pct": round((eq / start_eq - 1.0) * 100, 2),
                "end_eq": round(eq, 4),
                "n_trades": len(trades),
            }
        )
        print(f"    toolkit={toolkit_ret*100:+.2f}% eq={eq:.3f}", flush=True)

    if not path_eq:
        return {"name": name, "error": "no equity", "segments": reports}

    s0 = path_eq[0][1]
    series = [e / s0 for _, e in path_eq]
    bh_start = next(px for d, px in sorted(bh_by.items()) if d >= w_start)
    bh_end = next(px for d, px in sorted(bh_by.items(), reverse=True) if d <= w_end)
    bh_series = [px / bh_start for d, px in sorted(bh_by.items()) if w_start <= d <= w_end]
    mult = series[-1]
    return {
        "name": name,
        "return_pct": round((mult - 1) * 100, 2),
        "multiple": round(mult, 4),
        "mdd_pct": round(mdd(series) * 100, 2),
        "bh_return_pct": round((bh_end / bh_start - 1) * 100, 2),
        "bh_mdd_pct": round(mdd(bh_series) * 100, 2) if bh_series else None,
        "n_segments": len(segs),
        "n_ok": sum(1 for x in reports if "error" not in x),
        "segments": reports,
    }


def main() -> None:
    print("fetch candles…", flush=True)
    candles = fetch_days(want=3500)
    segs, _ = build_segments(candles)
    print(f"classifier segments={len(segs)}", flush=True)

    bh_raw = fetch_bh_days(want=3500)
    bh_by = {
        parse_d(c["candle_date_time_utc"]): float(c["trade_price"]) for c in bh_raw
    }

    CACHE.mkdir(parents=True, exist_ok=True)
    pc.CACHE = CACHE

    windows_out: dict = {}
    for wname, (w0, w1) in WINDOWS.items():
        print(f"\n=== {wname} {w0}→{w1} ===", flush=True)
        pc_segs = clip_segs(segs, w0, w1, POLICY_C)
        fam_segs = clip_segs(segs, w0, w1, FAMOUS)
        pc_res = run_map("policy_c", pc_segs, bh_by, w0, w1)
        fam_res = run_map("famous", fam_segs, bh_by, w0, w1)
        verdict = {}
        if "error" not in pc_res and "error" not in fam_res:
            verdict = {
                "famous_beats_pc_return": fam_res["return_pct"] > pc_res["return_pct"],
                "famous_better_mdd": fam_res["mdd_pct"] > pc_res["mdd_pct"],  # less negative
                "return_gap_pct_p": round(fam_res["return_pct"] - pc_res["return_pct"], 2),
                "mdd_gap_pct_p": round(fam_res["mdd_pct"] - pc_res["mdd_pct"], 2),
            }
        windows_out[wname] = {
            "start": w0.isoformat(),
            "end": w1.isoformat(),
            "policy_c": {k: v for k, v in pc_res.items() if k != "segments"},
            "famous": {k: v for k, v in fam_res.items() if k != "segments"},
            "verdict": verdict,
            "policy_c_segments": pc_res.get("segments"),
            "famous_segments": fam_res.get("segments"),
        }
        print(
            f"  PC  {pc_res.get('return_pct')}% mdd={pc_res.get('mdd_pct')}%\n"
            f"  FAM {fam_res.get('return_pct')}% mdd={fam_res.get('mdd_pct')}%\n"
            f"  {verdict}",
            flush=True,
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary = {
        "method": "same_regime_segments_toolkit_compound",
        "maps": {"policy_c": POLICY_C, "famous": FAMOUS},
        "windows": {
            k: {kk: vv for kk, vv in v.items() if not kk.endswith("_segments")}
            for k, v in windows_out.items()
        },
        "detail": windows_out,
    }
    out = OUT / f"bt-famous-vs-policyC-{stamp}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary["windows"], indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
