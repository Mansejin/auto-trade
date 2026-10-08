#!/usr/bin/env python3
"""Red-team Policy C: hindsight in regime segments, simple baselines, concentration.

Daily KRW-BTC only (Upbit public API, cached to _krwbtc_1d.json). No toolkit needed.
Position for day i (close[i-1] -> close[i]) is decided from data up to close[i-1],
except the 'hindsight' variants which reproduce how Policy C segments are built.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from scripts.regime_engine_v2 import build_segments, classify_day, fetch_days, series_adx, sma  # noqa: E402

FEE = 0.0005
CACHE = HERE / "_krwbtc_1d.json"
WINDOWS = {
    "IS 2021-07-27..2026-07-26": ("2021-07-27", "2026-07-26"),
    "OOS 2018-04-12..2021-07-24": ("2018-04-12", "2021-07-24"),
}
RISK_ON = {"bull", "transition"}


def load() -> list[dict]:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    c = fetch_days(want=3500)
    c = c[:-1]  # drop forming bar
    CACHE.write_text(json.dumps(c), encoding="utf-8")
    return c


def mdd(xs: list[float]) -> float:
    peak, worst = xs[0], 0.0
    for x in xs:
        peak = max(peak, x)
        worst = min(worst, x / peak - 1)
    return worst


def run_weights(closes, dates, w, a, b):
    """w[i] = BTC weight held over day i. Returns (ret, mdd, n_switch)."""
    idx = [i for i, d in enumerate(dates) if a <= d <= b]
    eq, series, prev, sw = 1.0, [1.0], w[idx[0]], 0
    for i in idx[1:]:
        r = closes[i] / closes[i - 1] - 1
        eq *= 1 + w[i] * r - FEE * abs(w[i] - prev)
        sw += w[i] != prev
        prev = w[i]
        series.append(eq)
    return eq - 1, mdd(series), sw


def run_5050(closes, dates, a, b, band=0.12, cd=30):
    idx = [i for i, d in enumerate(dates) if a <= d <= b]
    px = closes[idx[0]]
    btc, cash, last = 0.5 / px * (1 - FEE), 0.5, None
    series = [1.0]
    for i in idx[1:]:
        px = closes[i]
        eq = btc * px + cash
        wb = btc * px / eq
        d = date.fromisoformat(dates[i])
        if abs(wb - 0.5) > band and (last is None or (d - last).days >= cd):
            delta = 0.5 * eq - btc * px
            cash -= delta + FEE * abs(delta)
            btc += delta / px
            last = d
        series.append(btc * px + cash)
    return series[-1] - 1, mdd(series), None


def main() -> None:
    c = load()
    closes = [x["trade_price"] for x in c]
    highs = [x["high_price"] for x in c]
    lows = [x["low_price"] for x in c]
    dates = [x["candle_date_time_utc"][:10] for x in c]
    n = len(c)
    pdi, mdi, adx = series_adx(highs, lows, closes)
    labels = [classify_day(closes[i], sma(closes, 50, i), sma(closes, 200, i), adx[i], pdi[i], mdi[i]) for i in range(n)]
    s200 = [sma(closes, 200, i) for i in range(n)]

    segs, _ = build_segments(c)
    hind = ["warmup"] * n
    pos = {d: i for i, d in enumerate(dates)}
    for s in segs:
        for i in range(pos[s["start"]], pos[s["end"]] + 1):
            hind[i] = s["regime"]

    # causal 14-day confirmation: switch only after new raw label persisted 14 closes
    conf = ["warmup"] * n
    cur, run_lab, run_len = "warmup", None, 0
    for i in range(n):
        lab = labels[i]
        run_len = run_len + 1 if lab == run_lab else 1
        run_lab = lab
        if cur == "warmup" and lab != "warmup":
            cur = lab
        elif lab != cur and run_len >= 14:
            cur = lab
        conf[i] = cur

    on = lambda lab: 1.0 if lab in RISK_ON else 0.0  # noqa: E731
    W = {
        "regime proxy, hindsight segs (BT method)": [on(hind[i]) for i in range(n)],
        "regime proxy, raw label same day": [on(labels[i]) for i in range(n)],
        "regime proxy, raw label next day (live)": [0.0] + [on(labels[i - 1]) for i in range(1, n)],
        "regime proxy, 14d confirm next day": [0.0] + [on(conf[i - 1]) for i in range(1, n)],
        "BTC hold": [1.0] * n,
        "SMA200 filter (close>SMA200, next day)": [0.0] + [1.0 if s200[i - 1] and closes[i - 1] > s200[i - 1] else 0.0 for i in range(1, n)],
    }
    vt = [0.0] * n
    for i in range(31, n):
        rs = [closes[j] / closes[j - 1] - 1 for j in range(i - 30, i)]
        m = sum(rs) / 30
        vol = math.sqrt(sum((r - m) ** 2 for r in rs) / 29) * math.sqrt(365)
        vt[i] = min(1.0, 0.40 / vol) if vol > 0 else 1.0
    W["vol-target 40% (30d, cap 1x)"] = vt
    sma_half = [0.5 * x for x in W["SMA200 filter (close>SMA200, next day)"]]
    W["SMA200 filter @ 50% size"] = sma_half

    out: dict = {"windows": {}}
    for name, (a, b) in WINDOWS.items():
        rows = {}
        for k, w in W.items():
            r, m, sw = run_weights(closes, dates, w, a, b)
            rows[k] = {"ret_pct": round(r * 100, 1), "mdd_pct": round(m * 100, 1), "switches": sw}
        r, m, _ = run_5050(closes, dates, a, b)
        rows["50:50 rebalance (+-12%p, cd30)"] = {"ret_pct": round(r * 100, 1), "mdd_pct": round(m * 100, 1)}
        idx = [i for i, d in enumerate(dates) if a <= d <= b]
        diff = sum(hind[i] != (labels[i - 1]) for i in idx) / len(idx)
        rows["_hindsight_label_mismatch_vs_live_pct"] = round(diff * 100, 1)
        rows["_risk_on_mismatch_pct"] = round(
            sum(on(hind[i]) != on(labels[i - 1]) for i in idx) / len(idx) * 100, 1
        )
        out["windows"][name] = rows

    # concentration on archived segment returns
    def comp(xs):
        p = 1.0
        for x in xs:
            p *= 1 + x / 100
        return round((p - 1) * 100, 1)

    is_path = json.loads((HERE / "_policyC_path_is.json").read_text(encoding="utf-8-sig"))["path"]
    oos = json.loads((HERE / "_policyC_oos.json").read_text(encoding="utf-8-sig"))["segments"]
    for tag, rets, regs in (
        ("IS", [s["ret"] for s in is_path], [s["regime"] for s in is_path]),
        ("OOS", [s["strat_ret_pct"] for s in oos], [s["regime"] for s in oos]),
    ):
        srt = sorted(rets, reverse=True)
        by_reg = {}
        for r, g in zip(rets, regs):
            by_reg.setdefault(g, []).append(r)
        out[f"concentration_{tag}"] = {
            "n_segments": len(rets),
            "all": comp(rets),
            "top5": srt[:5],
            "without_top5": comp(srt[5:]),
            "without_top1": comp(srt[1:]),
            "by_regime": {g: comp(v) for g, v in by_reg.items()},
        }
    # min_run merge audit: segments whose regime differs from raw label on their start day
    out["segments_total"] = len(segs)
    out["segments_start_label_mismatch"] = sum(labels[pos[s["start"]]] != s["regime"] for s in segs)
    out["raw_label_changes_all_history"] = sum(
        1 for i in range(1, n) if labels[i] != labels[i - 1]
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))
    (HERE / "policyC_redteam_out.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
