#!/usr/bin/env python3
"""Falsify cal-event-sweep-fade-r3-v1 on Binance BTCUSDT-M 15m.

Frozen:
  events FOMC/CPI/NFP, vol gate first 60m range >= 2*ATR14,
  sweep = break of first-60m high/low then reclaim into range within 4 bars,
  side by regime (bull/transition long on failed downside sweep;
                 bear short on failed upside sweep; sideways skip),
  1-shot/window, SL=0.5% price, TP=1.5% (1:3), fee 0.06%*2.
"""
from __future__ import annotations

import json
import subprocess
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
OUT = ROOT / "reports"
SL = 0.005
TP = 0.015
ATR_K = 2.0
RECLAIM_BARS = 4
FEE_RT = 0.0006 * 2
HOLDOUT_FRAC = 0.30


def load_ohlcv(path: Path) -> pd.DataFrame:
    df = pd.read_feather(path)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df.sort_values("date").reset_index(drop=True)


def regime_by_day(m15: pd.DataFrame) -> pd.Series:
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
    s = pd.Series(labels, index=pd.to_datetime(d1["date"], utc=True).dt.normalize())
    return s.shift(1)


def atr14(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    prev = c.shift(1)
    tr = pd.concat([(h - l), (h - prev).abs(), (l - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def resolve_trade(side: str, entry: float, bars: pd.DataFrame) -> tuple[float, str, pd.Timestamp]:
    sl_px = entry * (1 - SL) if side == "long" else entry * (1 + SL)
    tp_px = entry * (1 + TP) if side == "long" else entry * (1 - TP)
    for _, b in bars.iterrows():
        hi, lo = float(b["high"]), float(b["low"])
        if side == "long":
            if lo <= sl_px:
                return sl_px, "sl", b.name
            if hi >= tp_px:
                return tp_px, "tp", b.name
        else:
            if hi >= sl_px:
                return sl_px, "sl", b.name
            if lo <= tp_px:
                return tp_px, "tp", b.name
    last = bars.iloc[-1]
    return float(last["close"]), "time", last.name


def simulate(events: list[dict], m15: pd.DataFrame, reg: pd.Series) -> list[dict]:
    m15 = m15.copy()
    m15["atr"] = atr14(m15, 14)
    idx = m15.set_index("date")
    out: list[dict] = []

    for ev in events:
        ts = pd.Timestamp(ev["ts_utc"], tz="UTC")
        day = ts.normalize()
        regime = reg.get(day, "warmup")
        if regime in ("sideways", "warmup", None) or (
            isinstance(regime, float) and np.isnan(regime)
        ):
            out.append({**ev, "status": "skip_regime", "regime": str(regime)})
            continue

        win = idx.loc[(idx.index >= ts) & (idx.index < ts + timedelta(hours=24))]
        if len(win) < 12:
            out.append({**ev, "status": "skip_nodata", "regime": regime})
            continue
        pre = idx.loc[idx.index < ts].tail(30)
        if pre.empty or pd.isna(pre["atr"].iloc[-1]):
            out.append({**ev, "status": "skip_atr", "regime": regime})
            continue
        atr0 = float(pre["atr"].iloc[-1])
        hour = win.iloc[:4]
        hi0, lo0 = float(hour["high"].max()), float(hour["low"].min())
        if (hi0 - lo0) < ATR_K * atr0:
            out.append({**ev, "status": "skip_vol", "regime": regime})
            continue

        # After first hour: look for sweep + reclaim within RECLAIM_BARS
        rest = win.iloc[4:]
        side = "long" if regime in ("bull", "transition") else "short"
        entered = False
        for i in range(len(rest)):
            row = rest.iloc[i]
            # sweep extremes vs first-hour box
            swept_low = float(row["low"]) < lo0
            swept_high = float(row["high"]) > hi0
            # reclaim window: this bar or next RECLAIM_BARS-1 closes back inside
            chunk = rest.iloc[i : i + RECLAIM_BARS]
            if chunk.empty:
                continue
            if side == "long" and swept_low:
                # failed downside sweep → long when close back >= lo0
                for j, b in chunk.iterrows():
                    if float(b["close"]) >= lo0:
                        entry = float(b["close"])
                        after = rest.loc[rest.index > j]
                        if after.empty:
                            break
                        exit_px, reason, exit_t = resolve_trade(side, entry, after)
                        ret = exit_px / entry - 1.0 - FEE_RT
                        out.append(
                            {
                                **ev,
                                "status": "traded",
                                "regime": regime,
                                "side": side,
                                "entry_ts": j.isoformat(),
                                "exit_ts": exit_t.isoformat(),
                                "entry": entry,
                                "exit": exit_px,
                                "reason": reason,
                                "ret_pct": round(ret * 100, 4),
                                "r_mult": round(ret / SL, 3),
                            }
                        )
                        entered = True
                        break
            elif side == "short" and swept_high:
                for j, b in chunk.iterrows():
                    if float(b["close"]) <= hi0:
                        entry = float(b["close"])
                        after = rest.loc[rest.index > j]
                        if after.empty:
                            break
                        exit_px, reason, exit_t = resolve_trade(side, entry, after)
                        ret = entry / exit_px - 1.0 - FEE_RT
                        out.append(
                            {
                                **ev,
                                "status": "traded",
                                "regime": regime,
                                "side": side,
                                "entry_ts": j.isoformat(),
                                "exit_ts": exit_t.isoformat(),
                                "entry": entry,
                                "exit": exit_px,
                                "reason": reason,
                                "ret_pct": round(ret * 100, 4),
                                "r_mult": round(ret / SL, 3),
                            }
                        )
                        entered = True
                        break
            if entered:
                break
        if not entered:
            out.append({**ev, "status": "skip_nosignal", "regime": regime, "side": side})
    return out


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
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_us_macro_calendar.py")], check=True
    )
    events = json.loads(CAL.read_text(encoding="utf-8"))["events"]
    m15 = load_ohlcv(FEATHER_15)
    reg = regime_by_day(m15)
    t0, t1 = m15["date"].min(), m15["date"].max()
    events = [e for e in events if t0 <= pd.Timestamp(e["ts_utc"], tz="UTC") <= t1]
    print(f"events={len(events)} {t0.date()}→{t1.date()}", flush=True)

    rows = simulate(events, m15, reg)
    traded = sorted(
        [t for t in rows if t["status"] == "traded"], key=lambda t: t["ts_utc"]
    )
    cut = int(len(traded) * (1 - HOLDOUT_FRAC))
    train, hold = traded[:cut], traded[cut:]
    summary = {
        "card": "cal-event-sweep-fade-r3-v1",
        "frozen": {
            "sl": SL,
            "tp": TP,
            "atr_k": ATR_K,
            "reclaim_bars": RECLAIM_BARS,
            "fee_rt": FEE_RT,
        },
        "n_events": len(events),
        "status_counts": pd.Series([t["status"] for t in rows]).value_counts().to_dict(),
        "all_traded": summarize(traded),
        "train_70": summarize(train),
        "holdout_30": summarize(hold),
    }
    h = summary["holdout_30"]
    if h.get("n", 0) < 8:
        summary["verdict"] = "UNDERPOWERED"
    elif h.get("pf_ge_1") and h.get("avg_pos"):
        summary["verdict"] = "SURVIVES_HOLDOUT"
    else:
        summary["verdict"] = "FALSIFIED"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = OUT / f"bt-cal-event-sweep-fade-r3-{stamp}.json"
    out.write_text(json.dumps({**summary, "trades": traded}, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
