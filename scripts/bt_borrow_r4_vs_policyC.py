#!/usr/bin/env python3
"""Borrow R1–R4 (Trend/Range × Vol) map from btcusdt-regime-multistrategy style.

Hard-switch onto our toolkit sleeves (no blend — Upbit JSON is one STRATEGY_PATH):
  R1 Trend+LowVol  → bull-v2
  R2 Trend+HighVol → bull-v2   (repo blends Donchian+EMA; we keep single trend sleeve)
  R3 Range+LowVol  → sideways-v5 MR
  R4 Range+HighVol → cash-flat (repo weight 0 — key borrow)

Race vs Policy C (bull/bear/side/transition map) on same calendar windows.
Frozen: ADX trend>=25 / range<25, HighVol = ATR14 > SMA20(ATR), min_run=3 days.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.regime_engine_v2 import fetch_days, series_adx, sma  # noqa: E402
import scripts.bt_policyC_continuous_equity as pc  # noqa: E402
from scripts.bt_policyC_continuous_equity import (  # noqa: E402
    mdd,
    parse_perf,
    parse_trades,
    run_segment_bt,
    segment_daily_equity_v2,
)
from scripts.bt_btc_cash_5050_rebalance import fetch_days as fetch_bh_days, parse_d  # noqa: E402
from scripts.regime_engine_v2 import build_segments  # noqa: E402

OUT = ROOT / "reports"
CACHE = ROOT / "reports/five-year/segment-csv-cache-r4-borrow"
MIN_RUN = 3
ADX_TREND = 25.0

POLICY_C = {
    "bull": "strategies/regime-bull-trend-4h-v2.json",
    "transition": "strategies/regime-bull-trend-4h-v2.json",
    "bear": "strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "strategies/regime-sideways-mr-4h-v5.json",
}
R4_MAP = {
    "R1": "strategies/regime-bull-trend-4h-v2.json",
    "R2": "strategies/regime-bull-trend-4h-v2.json",
    "R3": "strategies/regime-sideways-mr-4h-v5.json",
    "R4": "strategies/famous-cash-flat-1d.json",
}
WINDOWS = {
    "in_sample_5y": (date(2021, 7, 27), date(2026, 7, 26)),
    "oos_presample": (date(2018, 4, 12), date(2021, 7, 24)),
}


def true_range(h, l, prev_c):
    return max(h - l, abs(h - prev_c), abs(l - prev_c))


def series_atr(highs, lows, closes, period: int = 14):
    n = len(closes)
    tr = [None] * n
    for i in range(1, n):
        tr[i] = true_range(highs[i], lows[i], closes[i - 1])
    atr = [None] * n
    if n <= period:
        return atr
    # wilder-ish seed
    atr[period] = sum(tr[1 : period + 1]) / period
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def classify_r4(adx, atr, atr_sma) -> str | None:
    if adx is None or atr is None or atr_sma is None:
        return None
    trend = adx >= ADX_TREND
    high_vol = atr > atr_sma
    if trend and not high_vol:
        return "R1"
    if trend and high_vol:
        return "R2"
    if (not trend) and not high_vol:
        return "R3"
    return "R4"


def build_r4_segments(candles: list[dict], min_run: int = MIN_RUN) -> list[dict]:
    closes = [c["trade_price"] for c in candles]
    highs = [c["high_price"] for c in candles]
    lows = [c["low_price"] for c in candles]
    dates = [c["candle_date_time_utc"][:10] for c in candles]
    _, _, adx = series_adx(highs, lows, closes)
    atr = series_atr(highs, lows, closes, 14)
    atr_sma: list[float | None] = [None] * len(atr)
    for i in range(len(atr)):
        if i + 1 < 20 or atr[i] is None:
            continue
        window = atr[i + 1 - 20 : i + 1]
        if any(x is None for x in window):
            continue
        atr_sma[i] = sum(window) / 20  # type: ignore[arg-type]

    labels = [classify_r4(adx[i], atr[i], atr_sma[i]) for i in range(len(closes))]

    raw = []
    cur = None
    for i, lab in enumerate(labels):
        if lab is None:
            continue
        if cur is None or lab != cur["regime"]:
            if cur:
                raw.append(cur)
            cur = {"start": dates[i], "end": dates[i], "regime": lab, "i0": i, "i1": i}
        else:
            cur["end"] = dates[i]
            cur["i1"] = i
    if cur:
        raw.append(cur)

    merged: list[dict] = []
    for s in raw:
        s["days"] = s["i1"] - s["i0"] + 1
        if merged and s["days"] < min_run:
            prev = merged[-1]
            prev["end"] = s["end"]
            prev["i1"] = s["i1"]
            prev["days"] = prev["i1"] - prev["i0"] + 1
            # keep prev regime (absorb short blips) — repo min_run smoothing
        elif merged and merged[-1]["regime"] == s["regime"]:
            prev = merged[-1]
            prev["end"] = s["end"]
            prev["i1"] = s["i1"]
            prev["days"] = prev["i1"] - prev["i0"] + 1
        else:
            merged.append(dict(s))

    segs = []
    for s in merged:
        segs.append(
            {
                "start": s["start"],
                "end": s["end"],
                "regime": s["regime"],
                "days": s["days"],
                "file": R4_MAP[s["regime"]],
            }
        )
    return segs


def clip_segs(segs: list[dict], start: date, end: date) -> list[dict]:
    out = []
    for s in segs:
        a, b = parse_d(s["start"]), parse_d(s["end"])
        if b < start or a > end:
            continue
        lo, hi = max(a, start), min(b, end)
        if (hi - lo).days < 5:
            continue
        out.append(
            {
                **s,
                "start": lo.isoformat(),
                "end": hi.isoformat(),
                "days": (hi - lo).days + 1,
            }
        )
    return out


def run_map(name: str, segs: list[dict], bh_by: dict, w0: date, w1: date) -> dict:
    eq = 1.0
    path_eq: list[tuple[date, float]] = []
    reports = []
    for i, seg in enumerate(segs):
        s, e = seg["start"], seg["end"]
        print(
            f"  [{name} {i+1}/{len(segs)}] {seg['regime']} {s}→{e} {Path(seg['file']).stem}",
            flush=True,
        )
        try:
            csv_path = run_segment_bt(seg["file"], s, e)
            time.sleep(0.7)
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
        day_list = []
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
            reports.append({**seg, "error": "empty"})
            continue
        if path_eq and piece[0][0] == path_eq[-1][0]:
            piece = piece[1:]
        eq = piece[-1][1]
        path_eq.extend(piece)
        reports.append(
            {
                **seg,
                "toolkit_ret_pct": round(toolkit_ret * 100, 2),
                "end_eq": round(eq, 4),
            }
        )
        print(f"    toolkit={toolkit_ret*100:+.2f}% eq={eq:.3f}", flush=True)

    if not path_eq:
        return {"name": name, "error": "no equity", "segments": reports}
    s0 = path_eq[0][1]
    series = [e / s0 for _, e in path_eq]
    bh_start = next(px for d, px in sorted(bh_by.items()) if d >= w0)
    bh_end = next(px for d, px in sorted(bh_by.items(), reverse=True) if d <= w1)
    bh_series = [px / bh_start for d, px in sorted(bh_by.items()) if w0 <= d <= w1]
    mult = series[-1]
    return {
        "name": name,
        "return_pct": round((mult - 1) * 100, 2),
        "multiple": round(mult, 4),
        "mdd_pct": round(mdd(series) * 100, 2),
        "bh_return_pct": round((bh_end / bh_start - 1) * 100, 2),
        "bh_mdd_pct": round(mdd(bh_series) * 100, 2),
        "n_ok": sum(1 for x in reports if "error" not in x),
        "n_segments": len(segs),
        "segments": reports,
    }


def policy_c_segs(candles, w0, w1):
    segs, _ = build_segments(candles)
    out = []
    for s in segs:
        a, b = parse_d(s["start"]), parse_d(s["end"])
        if b < w0 or a > w1:
            continue
        lo, hi = max(a, w0), min(b, w1)
        if (hi - lo).days < 5:
            continue
        regime = s["regime"]
        if regime not in POLICY_C:
            continue
        out.append(
            {
                "start": lo.isoformat(),
                "end": hi.isoformat(),
                "regime": regime,
                "file": POLICY_C[regime],
                "days": (hi - lo).days + 1,
            }
        )
    return out


def main() -> None:
    print("fetch candles…", flush=True)
    candles = fetch_days(want=3500)
    r4_all = build_r4_segments(candles)
    print(f"R4 segments={len(r4_all)}", flush=True)

    bh_raw = fetch_bh_days(want=3500)
    bh_by = {
        parse_d(c["candle_date_time_utc"]): float(c["trade_price"]) for c in bh_raw
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    pc.CACHE = CACHE

    windows_out = {}
    for wname, (w0, w1) in WINDOWS.items():
        print(f"\n=== {wname} {w0}→{w1} ===", flush=True)
        pc_segs = policy_c_segs(candles, w0, w1)
        r4_segs = clip_segs(r4_all, w0, w1)
        # recount regimes
        from collections import Counter

        print("  PolicyC regimes", Counter(s["regime"] for s in pc_segs), flush=True)
        print("  R4 regimes", Counter(s["regime"] for s in r4_segs), flush=True)
        pc_res = run_map("policy_c", pc_segs, bh_by, w0, w1)
        r4_res = run_map("r4_borrow", r4_segs, bh_by, w0, w1)
        verdict = {}
        if "error" not in pc_res and "error" not in r4_res:
            verdict = {
                "r4_beats_pc_return": r4_res["return_pct"] > pc_res["return_pct"],
                "r4_better_mdd": r4_res["mdd_pct"] > pc_res["mdd_pct"],
                "return_gap_pct_p": round(r4_res["return_pct"] - pc_res["return_pct"], 2),
                "mdd_gap_pct_p": round(r4_res["mdd_pct"] - pc_res["mdd_pct"], 2),
            }
        windows_out[wname] = {
            "policy_c": {k: v for k, v in pc_res.items() if k != "segments"},
            "r4_borrow": {k: v for k, v in r4_res.items() if k != "segments"},
            "verdict": verdict,
            "policy_c_segments": pc_res.get("segments"),
            "r4_segments": r4_res.get("segments"),
        }
        print(f"  PC  {pc_res.get('return_pct')}% mdd={pc_res.get('mdd_pct')}%", flush=True)
        print(f"  R4  {r4_res.get('return_pct')}% mdd={r4_res.get('mdd_pct')}%", flush=True)
        print(f"  {verdict}", flush=True)

    # survive borrow only if both windows: better MDD without catastrophic return loss
    # OR beats PC return both — strict: must not lose return on both while claiming upgrade
    def ok(w):
        v = windows_out[w]["verdict"]
        pc = windows_out[w]["policy_c"]
        r4 = windows_out[w]["r4_borrow"]
        if not v:
            return False
        # prefer: better or equal return and better MDD, or clearly better risk-adj
        return (r4["return_pct"] >= pc["return_pct"] * 0.9) and (
            r4["mdd_pct"] > pc["mdd_pct"]
        )

    summary = {
        "card": "borrow-r4-trend-vol-map-v1",
        "source": "quantsarahz/btcusdt-regime-multistrategy-trading style R1-R4",
        "frozen": {
            "adx_trend": ADX_TREND,
            "high_vol": "ATR14 > SMA20(ATR)",
            "min_run_days": MIN_RUN,
            "map": R4_MAP,
        },
        "windows": {
            k: {kk: vv for kk, vv in v.items() if not kk.endswith("segments")}
            for k, v in windows_out.items()
        },
        "verdict": "SURVIVES_VS_POLICY_C"
        if all(ok(w) for w in WINDOWS)
        else "FALSIFIED_VS_POLICY_C",
        "detail": windows_out,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = OUT / f"bt-borrow-r4-vs-policyC-{stamp}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary["windows"], indent=2))
    print("VERDICT", summary["verdict"])
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
