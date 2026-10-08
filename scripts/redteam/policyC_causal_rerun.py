#!/usr/bin/env python3
"""Rerun Policy C segment chain with the toolkit under hindsight vs causal segmentation.

Variants (same frozen map, same toolkit, same stitching as bt_policyC_continuous_equity):
  hindsight   : build_segments (label uses day-i close, BT starts day-i 00:00; <14d runs merged)
  hind_shift1 : same segments, every boundary moved +1 day (removes same-day close peek only)
  live_raw    : regime = raw label of previous closed day (what remote_regime_switch does daily)
  live_conf14 : causal 14-day persistence before switching (honest version of min_run)
Bull and transition share a file, so adjacent bull/transition days are one segment in causal variants.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from scripts.bt_policyC_continuous_equity import mdd, parse_perf, parse_trades, segment_daily_equity_v2  # noqa: E402
from scripts.regime_engine_v2 import build_segments, classify_day, series_adx, sma  # noqa: E402
from scripts.toolkit_bt import run_many  # noqa: E402

CACHE = HERE / "_bt_cache"
MAP = {
    "bull": "strategies/regime-bull-trend-4h-v2.json",
    "transition": "strategies/regime-bull-trend-4h-v2.json",
    "bear": "strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "strategies/regime-sideways-mr-4h-v5.json",
}
WINDOWS = {"IS": ("2021-07-27", "2026-07-26"), "OOS": ("2018-04-12", "2021-07-24")}


def runs(dates, regs, a, b, merge_files=True):
    out = []
    for d, g in zip(dates, regs):
        if not (a <= d <= b) or g not in MAP:
            continue
        key = MAP[g] if merge_files else g
        if out and out[-1]["key"] == key and out[-1]["end_next"] == d:
            out[-1]["end"] = d
        else:
            out.append({"key": key, "start": d, "end": d, "regime": g, "file": MAP[g]})
        out[-1]["end_next"] = (date.fromisoformat(d) + timedelta(days=1)).isoformat()
    return out


def chain(segs, closes_by):
    jobs = [(s["file"], s["start"], s["end"]) for s in segs]
    paths = run_many(jobs, cache_dir=CACHE, workers=4)
    eq, curve, rets = 1.0, [], []
    for s, p in zip(segs, paths):
        tr = float(parse_perf(p).get("total_return_pct", "0").replace("+", "")) / 100
        rets.append(tr)
        days = []
        d = date.fromisoformat(s["start"])
        while d <= date.fromisoformat(s["end"]):
            if d.isoformat() in closes_by:
                days.append((d, closes_by[d.isoformat()]))
            d += timedelta(days=1)
        piece = segment_daily_equity_v2(parse_trades(p), days, eq, 1 + tr) if days else []
        if piece:
            curve.extend(v for _, v in piece)
            eq = piece[-1][1]
        else:
            eq *= 1 + tr
    return {"ret_pct": round((eq - 1) * 100, 1), "mdd_pct": round(mdd([1.0] + curve) * 100, 1),
            "n_segments": len(segs)}


def main() -> None:
    c = json.loads((HERE / "_krwbtc_1d.json").read_text(encoding="utf-8"))
    closes = [x["trade_price"] for x in c]
    dates = [x["candle_date_time_utc"][:10] for x in c]
    n = len(c)
    pdi, mdi, adx = series_adx([x["high_price"] for x in c], [x["low_price"] for x in c], closes)
    labels = [classify_day(closes[i], sma(closes, 50, i), sma(closes, 200, i), adx[i], pdi[i], mdi[i]) for i in range(n)]
    hind = ["warmup"] * n
    pos = {d: i for i, d in enumerate(dates)}
    for s in build_segments(c)[0]:
        for i in range(pos[s["start"]], pos[s["end"]] + 1):
            hind[i] = s["regime"]
    conf, cur, rl, ln = ["warmup"] * n, "warmup", None, 0
    for i, lab in enumerate(labels):
        ln = ln + 1 if lab == rl else 1
        rl = lab
        if (cur == "warmup" and lab != "warmup") or (lab != cur and ln >= 14):
            cur = lab
        conf[i] = cur
    closes_by = dict(zip(dates, closes))

    variants = {
        "hindsight": (hind, False),
        "hind_shift1": (["warmup"] + hind[:-1], False),
        "live_raw": (["warmup"] + labels[:-1], True),
        "live_conf14": (["warmup"] + conf[:-1], True),
    }
    out = {}
    for w, (a, b) in WINDOWS.items():
        for k, (regs, mf) in variants.items():
            segs = runs(dates, regs, a, b, merge_files=mf)
            print(f"{w} {k}: {len(segs)} segments", flush=True)
            out[f"{w} {k}"] = chain(segs, closes_by)
            print(out[f"{w} {k}"], flush=True)
    (HERE / "policyC_causal_rerun_out.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
