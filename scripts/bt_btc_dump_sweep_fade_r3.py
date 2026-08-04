#!/usr/bin/env python3
"""Falsify btc-dump-sweep-fade-r3-v1 on Binance BTCUSDT-M 15m (always-on).

Frozen:
  dump = 4-bar low breaks prior 20-bar low AND drop from 4-bar high >= 2*ATR14
  long reclaim = close back above broken level within 4 bars
  regime: bull/transition only (bear/sideways skip)
  1-shot + cooldown 6h after any trade/skip resolve
  SL 0.5% / TP 1.5% (1:3), fee 0.06%*2
  train/holdout by time 70/30 on trades
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

FEATHER_15 = (
    ROOT
    / "freqtrade-research/user_data/data/binance/futures/BTC_USDT_USDT-15m-futures.feather"
)
OUT = ROOT / "reports"
SL = 0.005
TP = 0.015
ATR_K = 2.0
LOOK_N = 4
PRIOR_N = 20
RECLAIM_BARS = 4
COOLDOWN = timedelta(hours=6)
FEE_RT = 0.0006 * 2
HOLDOUT_FRAC = 0.30


def load_m15() -> pd.DataFrame:
    df = pd.read_feather(FEATHER_15)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df.sort_values("date").reset_index(drop=True)


def attach_regime(m15: pd.DataFrame) -> pd.DataFrame:
    x = m15.set_index("date")
    d1 = (
        x.resample("1D")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna(subset=["close"])
        .reset_index()
    )
    closes = d1["close"].tolist()
    highs = d1["high"].tolist()
    lows = d1["low"].tolist()
    pdi, mdi, adx = series_adx(highs, lows, closes)
    labels = [
        classify_day(
            closes[i], sma(closes, 50, i), sma(closes, 200, i), adx[i], pdi[i], mdi[i]
        )
        for i in range(len(closes))
    ]
    reg = pd.Series(labels, index=pd.to_datetime(d1["date"], utc=True).dt.normalize())
    reg = reg.shift(1)
    m15 = m15.copy()
    day = m15["date"].dt.normalize()
    m15["regime"] = day.map(reg).fillna("warmup")
    return m15


def atr_series(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    prev = c.shift(1)
    tr = pd.concat([(h - l), (h - prev).abs(), (l - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def resolve(entry: float, bars: pd.DataFrame) -> tuple[float, str, pd.Timestamp]:
    sl_px = entry * (1 - SL)
    tp_px = entry * (1 + TP)
    for _, b in bars.iterrows():
        if float(b["low"]) <= sl_px:
            return sl_px, "sl", b.name
        if float(b["high"]) >= tp_px:
            return tp_px, "tp", b.name
    last = bars.iloc[-1]
    return float(last["close"]), "time", last.name


def simulate(df: pd.DataFrame) -> list[dict]:
    df = df.copy()
    df["atr"] = atr_series(df)
    df["prior_low"] = df["low"].rolling(PRIOR_N).min().shift(1)
    idx = df.set_index("date")
    trades: list[dict] = []
    i = PRIOR_N + LOOK_N + 20
    n = len(df)
    cooldown_until: pd.Timestamp | None = None

    while i < n - RECLAIM_BARS - 2:
        ts = df.at[i, "date"]
        if cooldown_until is not None and ts < cooldown_until:
            i += 1
            continue
        regime = df.at[i, "regime"]
        if regime not in ("bull", "transition"):
            i += 1
            continue
        atr = df.at[i, "atr"]
        prior_low = df.at[i, "prior_low"]
        if pd.isna(atr) or pd.isna(prior_low):
            i += 1
            continue
        window = df.iloc[i - LOOK_N + 1 : i + 1]
        w_low = float(window["low"].min())
        w_high = float(window["high"].max())
        dump = w_low < float(prior_low) and (w_high - w_low) >= ATR_K * float(atr)
        if not dump:
            i += 1
            continue
        level = float(prior_low)
        # reclaim in next RECLAIM_BARS (exclusive of signal bar end — start at i)
        entered = False
        for j in range(i, min(i + RECLAIM_BARS, n)):
            if float(df.at[j, "close"]) >= level:
                entry_t = df.at[j, "date"]
                entry = float(df.at[j, "close"])
                after = idx.loc[idx.index > entry_t]
                # cap path to 24h
                after = after.loc[after.index <= entry_t + timedelta(hours=24)]
                if len(after) < 2:
                    break
                exit_px, reason, exit_t = resolve(entry, after)
                ret = exit_px / entry - 1.0 - FEE_RT
                trades.append(
                    {
                        "entry_ts": entry_t.isoformat(),
                        "exit_ts": exit_t.isoformat(),
                        "regime": regime,
                        "level": level,
                        "entry": entry,
                        "exit": exit_px,
                        "reason": reason,
                        "ret_pct": round(ret * 100, 4),
                        "r_mult": round(ret / SL, 3),
                    }
                )
                cooldown_until = entry_t + COOLDOWN
                # jump index to after exit roughly
                i = int(df.index[df["date"] >= exit_t][0]) + 1 if any(df["date"] >= exit_t) else j + 1
                entered = True
                break
        if not entered:
            cooldown_until = ts + COOLDOWN
            i += 1
    return trades


def summarize(traded: list[dict]) -> dict:
    if not traded:
        return {"n": 0}
    rets = [t["ret_pct"] / 100 for t in traded]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    gp, gl = sum(wins), abs(sum(losses))
    eq = peak = 1.0
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
        "pf_ge_1": bool(gl > 0 and gp / gl >= 1),
        "avg_pos": bool(float(np.mean(rets)) > 0),
    }


def main() -> None:
    print("load…", flush=True)
    m15 = attach_regime(load_m15())
    print(f"bars={len(m15)} {m15['date'].iloc[0].date()}→{m15['date'].iloc[-1].date()}", flush=True)
    traded = simulate(m15)
    traded.sort(key=lambda t: t["entry_ts"])
    cut = int(len(traded) * (1 - HOLDOUT_FRAC))
    train, hold = traded[:cut], traded[cut:]
    summary = {
        "card": "btc-dump-sweep-fade-r3-v1",
        "frozen": {
            "sl": SL,
            "tp": TP,
            "atr_k": ATR_K,
            "look_n": LOOK_N,
            "prior_n": PRIOR_N,
            "reclaim_bars": RECLAIM_BARS,
            "cooldown_h": 6,
            "fee_rt": FEE_RT,
            "regime": "bull_transition_long_only",
        },
        "all_traded": summarize(traded),
        "train_70": summarize(train),
        "holdout_30": summarize(hold),
    }
    h, t = summary["holdout_30"], summary["train_70"]
    if h.get("n", 0) < 20:
        summary["verdict"] = "UNDERPOWERED"
    elif h.get("pf_ge_1") and h.get("avg_pos") and t.get("pf_ge_1"):
        summary["verdict"] = "SURVIVES"
    elif h.get("pf_ge_1") and h.get("avg_pos"):
        summary["verdict"] = "SURVIVES_HOLDOUT_ONLY"
    else:
        summary["verdict"] = "FALSIFIED"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = OUT / f"bt-btc-dump-sweep-fade-r3-{stamp}.json"
    out.write_text(json.dumps({**summary, "trades": traded}, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
