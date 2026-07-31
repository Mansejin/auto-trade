#!/usr/bin/env python3
"""Falsify cal-event-vol-reclaim-r10-v1 on Binance BTCUSDT-M 15m.

Frozen: FOMC/CPI/NFP, SL=0.4%, TP=4%, ATR k=2, 1-shot/window, sideways=skip,
regime from daily engine v2 (prior day), fee 0.06%×2. Leverage not in PnL %
(price R:R only; lev is sizing for LIVE).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.regime_engine_v2 import classify_day, series_adx, sma  # noqa: E402

CAL = ROOT / "config" / "us-macro-calendar.json"
FEATHER_15 = (
    ROOT
    / "freqtrade-research/user_data/data/binance/futures/BTC_USDT_USDT-15m-futures.feather"
)
FEATHER_1D = (
    ROOT
    / "freqtrade-research/user_data/data/binance/futures/BTC_USDT_USDT-1d-futures.feather"
)
OUT = ROOT / "reports"
SL = 0.004
TP = 0.04
ATR_K = 2.0
FEE_RT = 0.0006 * 2
HOLDOUT_FRAC = 0.30


def load_ohlcv(path: Path) -> pd.DataFrame:
    df = pd.read_feather(path)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df.sort_values("date").reset_index(drop=True)


def regime_series(d1: pd.DataFrame) -> pd.Series:
    closes = d1["close"].tolist()
    highs = d1["high"].tolist()
    lows = d1["low"].tolist()
    pdi, mdi, adx = series_adx(highs, lows, closes)
    labels = []
    for i in range(len(closes)):
        labels.append(
            classify_day(
                closes[i],
                sma(closes, 50, i),
                sma(closes, 200, i),
                adx[i],
                pdi[i],
                mdi[i],
            )
        )
    # prior closed day → shift 1
    s = pd.Series(labels, index=d1["date"])
    return s.shift(1)


def atr14(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    prev = c.shift(1)
    tr = pd.concat([(h - l), (h - prev).abs(), (l - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def simulate(events: list[dict], m15: pd.DataFrame, reg_by_day: pd.Series) -> list[dict]:
    m15 = m15.copy()
    m15["ema20"] = m15["close"].ewm(span=20, adjust=False).mean()
    m15["atr"] = atr14(m15, 14)
    idx = m15.set_index("date")
    trades: list[dict] = []

    for ev in events:
        ts = pd.Timestamp(ev["ts_utc"])
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        day = ts.floor("D")
        regime = reg_by_day.get(day)
        if regime is None:
            # try date match on index
            hits = reg_by_day.index[reg_by_day.index.normalize() == day]
            regime = reg_by_day.loc[hits[0]] if len(hits) else "warmup"
        if regime in ("sideways", "warmup", None) or (isinstance(regime, float) and np.isnan(regime)):
            trades.append({**ev, "status": "skip_regime", "regime": regime})
            continue

        win_end = ts + timedelta(hours=24)
        window = idx.loc[(idx.index >= ts) & (idx.index < win_end)]
        if len(window) < 8:
            trades.append({**ev, "status": "skip_nodata", "regime": regime})
            continue

        pre = idx.loc[idx.index < ts].tail(30)
        if pre.empty or pd.isna(pre["atr"].iloc[-1]):
            trades.append({**ev, "status": "skip_atr", "regime": regime})
            continue
        atr0 = float(pre["atr"].iloc[-1])
        first_hour = window.iloc[:4]  # 4×15m
        rng = float(first_hour["high"].max() - first_hour["low"].min())
        if rng < ATR_K * atr0:
            trades.append({**ev, "status": "skip_vol", "regime": regime, "rng": rng, "atr": atr0})
            continue

        side = "long" if regime in ("bull", "transition") else "short"
        entered = False
        entry_px = entry_t = None
        # scan after first hour for 1-shot cross
        scan = window.iloc[4:]
        for i in range(1, len(scan)):
            row, prev = scan.iloc[i], scan.iloc[i - 1]
            if side == "long":
                cross = prev["close"] <= prev["ema20"] and row["close"] > row["ema20"]
            else:
                cross = prev["close"] >= prev["ema20"] and row["close"] < row["ema20"]
            if not cross:
                continue
            entered = True
            entry_px = float(row["close"])
            entry_t = row.name
            rest = scan.iloc[i + 1 :]
            sl_px = entry_px * (1 - SL) if side == "long" else entry_px * (1 + SL)
            tp_px = entry_px * (1 + TP) if side == "long" else entry_px * (1 - TP)
            exit_px = exit_reason = exit_t = None
            for _, b in rest.iterrows():
                hi, lo, cl = float(b["high"]), float(b["low"]), float(b["close"])
                if side == "long":
                    if lo <= sl_px:
                        exit_px, exit_reason, exit_t = sl_px, "sl", b.name
                        break
                    if hi >= tp_px:
                        exit_px, exit_reason, exit_t = tp_px, "tp", b.name
                        break
                else:
                    if hi >= sl_px:
                        exit_px, exit_reason, exit_t = sl_px, "sl", b.name
                        break
                    if lo <= tp_px:
                        exit_px, exit_reason, exit_t = tp_px, "tp", b.name
                        break
            if exit_px is None:
                last = scan.iloc[-1]
                exit_px, exit_reason, exit_t = float(last["close"]), "time", last.name
            if side == "long":
                ret = exit_px / entry_px - 1.0
            else:
                ret = entry_px / exit_px - 1.0
            ret_net = ret - FEE_RT
            r_mult = ret_net / SL
            trades.append(
                {
                    **ev,
                    "status": "traded",
                    "regime": regime,
                    "side": side,
                    "entry_ts": entry_t.isoformat(),
                    "exit_ts": exit_t.isoformat() if hasattr(exit_t, "isoformat") else str(exit_t),
                    "entry": entry_px,
                    "exit": exit_px,
                    "reason": exit_reason,
                    "ret_pct": round(ret_net * 100, 4),
                    "r_mult": round(r_mult, 3),
                }
            )
            break
        if not entered:
            trades.append({**ev, "status": "skip_nosignal", "regime": regime, "side": side})
    return trades


def summarize(traded: list[dict]) -> dict:
    if not traded:
        return {"n": 0}
    rets = [t["ret_pct"] / 100 for t in traded]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    gp = sum(wins)
    gl = abs(sum(losses))
    eq = 1.0
    peak = 1.0
    mdd = 0.0
    for r in rets:
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    return {
        "n": len(traded),
        "win_rate": round(len(wins) / len(traded) * 100, 2),
        "avg_ret_pct": round(float(np.mean(rets) * 100), 4),
        "sum_ret_compound_pct": round((eq - 1) * 100, 2),
        "pf": round(gp / gl, 3) if gl > 0 else None,
        "mdd_pct": round(mdd * 100, 2),
        "tp": sum(1 for t in traded if t["reason"] == "tp"),
        "sl": sum(1 for t in traded if t["reason"] == "sl"),
        "time": sum(1 for t in traded if t["reason"] == "time"),
        "median_r": round(float(np.median([t["r_mult"] for t in traded])), 3),
        "beats_breakeven_wr": bool(len(wins) / len(traded) >= 0.12),
        "pf_ge_1": bool((gp / gl) >= 1) if gl > 0 else False,
    }


def main() -> None:
    # ensure calendar
    import subprocess

    subprocess.run([sys.executable, str(ROOT / "scripts/build_us_macro_calendar.py")], check=True)
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    events = cal["events"]
    m15 = load_ohlcv(FEATHER_15)
    d1 = load_ohlcv(FEATHER_1D)
    # if 1d short, resample from 15m
    if len(d1) < 250:
        print("1d short — resampling from 15m", flush=True)
        x = m15.set_index("date")
        d1 = (
            x.resample("1D")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna(subset=["close"])
            .reset_index()
        )
    reg = regime_series(d1)
    # align index to midnight UTC dates
    reg.index = pd.to_datetime(reg.index, utc=True).normalize()

    t0 = m15["date"].min()
    t1 = m15["date"].max()
    events = [
        e
        for e in events
        if t0 <= pd.Timestamp(e["ts_utc"], tz="UTC") <= t1
    ]
    print(f"events in data range: {len(events)} ({t0.date()}→{t1.date()})", flush=True)

    all_rows = simulate(events, m15, reg)
    traded = [t for t in all_rows if t.get("status") == "traded"]
    traded.sort(key=lambda t: t["ts_utc"])
    cut = int(len(traded) * (1 - HOLDOUT_FRAC))
    train, hold = traded[:cut], traded[cut:]

    summary = {
        "card": "cal-event-vol-reclaim-r10-v1",
        "data": str(FEATHER_15),
        "range": [str(t0), str(t1)],
        "frozen": {"sl": SL, "tp": TP, "atr_k": ATR_K, "fee_rt": FEE_RT, "events": ["FOMC", "CPI", "NFP"]},
        "n_events": len(events),
        "status_counts": pd.Series([t["status"] for t in all_rows]).value_counts().to_dict(),
        "all_traded": summarize(traded),
        "train_70": summarize(train),
        "holdout_30": summarize(hold),
        "verdict": None,
    }
    h = summary["holdout_30"]
    if h.get("n", 0) < 8:
        summary["verdict"] = "UNDERPOWERED"
    elif h.get("pf_ge_1") and h.get("avg_ret_pct", 0) > 0:
        summary["verdict"] = "SURVIVES_HOLDOUT"
    else:
        summary["verdict"] = "FALSIFIED"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_json = OUT / f"bt-cal-event-vol-r10-{stamp}.json"
    out_json.write_text(json.dumps({**summary, "trades": traded}, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k != "trades"}, indent=2))
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()
