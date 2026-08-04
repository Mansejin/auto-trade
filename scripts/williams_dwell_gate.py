#!/usr/bin/env python3
"""Williams sideways mount gate — research helper (no orders).

Computes daily regime + sideways dwell from Binance BTCUSDT-M 1d feather
(or any OHLCV feather with date/open/high/low/close).

Mount modes (frozen research contracts):
  off      — never
  raw      — regime==sideways (1h strategy ADX filter still applies in JSON)
  dwell7   — sideways and dwell >= 7
  dwell14  — sideways and dwell >= 14
  hybrid   — dwell 7..13 => early_strict slug; dwell >=14 => base williams slug

Does not touch LIVE / Policy C.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FEATHER = (
    ROOT
    / "freqtrade-research"
    / "user_data"
    / "data"
    / "binance"
    / "futures"
    / "BTC_USDT_USDT-1d-futures.feather"
)
BASE_SLUG = "regime-sideways-mr-1h-williams-v1"
EARLY_SLUG = "regime-sideways-mr-1h-williams-early-strict-v2"


def _classify_rows(feather: Path):
    import pandas as pd
    import talib.abstract as ta

    inf = pd.read_feather(feather).sort_values("date").reset_index(drop=True)
    inf["sma50"] = ta.SMA(inf, timeperiod=50)
    inf["sma200"] = ta.SMA(inf, timeperiod=200)
    inf["adx_d"] = ta.ADX(inf, timeperiod=14)
    inf["pdi"] = ta.PLUS_DI(inf, timeperiod=14)
    inf["mdi"] = ta.MINUS_DI(inf, timeperiod=14)
    sideways = inf["adx_d"] < 20
    bull = (
        (inf["close"] > inf["sma200"])
        & (inf["sma50"] > inf["sma200"])
        & (inf["pdi"] >= inf["mdi"])
        & (~sideways)
    )
    bear = (
        (inf["close"] < inf["sma200"])
        & (inf["sma50"] < inf["sma200"])
        & (inf["close"] < inf["sma50"])
        & (inf["mdi"] > inf["pdi"])
        & (~sideways)
    )

    def label(i: int) -> str:
        if bool(sideways.iloc[i]):
            return "sideways"
        if bool(bull.iloc[i]):
            return "bull"
        if bool(bear.iloc[i]):
            return "bear"
        return "transition"

    rows = []
    for i in range(len(inf) - 1):
        d = pd.Timestamp(inf.loc[i + 1, "date"]).tz_convert("UTC").normalize()
        rows.append({"date": d, "regime": label(i)})
    import pandas as pd

    df = pd.DataFrame(rows)
    dwell = 0
    ds = []
    for r in df["regime"]:
        dwell = dwell + 1 if r == "sideways" else 0
        ds.append(dwell)
    df["dwell"] = ds
    return df


def decide(mode: str, regime: str, dwell: int) -> dict:
    if mode == "off" or regime != "sideways":
        return {"allow": False, "slug": None, "reason": f"regime={regime}"}
    if mode == "raw":
        return {"allow": True, "slug": BASE_SLUG, "reason": "sideways raw"}
    if mode == "dwell7":
        ok = dwell >= 7
        return {
            "allow": ok,
            "slug": BASE_SLUG if ok else None,
            "reason": f"dwell={dwell} need>=7",
        }
    if mode == "dwell14":
        ok = dwell >= 14
        return {
            "allow": ok,
            "slug": BASE_SLUG if ok else None,
            "reason": f"dwell={dwell} need>=14",
        }
    if mode == "hybrid":
        if dwell >= 14:
            return {"allow": True, "slug": BASE_SLUG, "reason": f"mature dwell={dwell}"}
        if dwell >= 7:
            return {
                "allow": True,
                "slug": EARLY_SLUG,
                "reason": f"early dwell={dwell} strict ADX<15",
            }
        return {"allow": False, "slug": None, "reason": f"dwell={dwell} <7"}
    raise SystemExit(f"unknown mode {mode}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feather", type=Path, default=DEFAULT_FEATHER)
    ap.add_argument(
        "--mode",
        choices=["off", "raw", "dwell7", "dwell14", "hybrid"],
        default="hybrid",
    )
    ap.add_argument("--date", help="UTC YYYY-MM-DD (default: today UTC)")
    args = ap.parse_args()
    if not args.feather.exists():
        print(json.dumps({"ok": False, "error": f"missing {args.feather}"}))
        return 1
    df = _classify_rows(args.feather)
    if args.date:
        day = __import__("pandas").Timestamp(args.date, tz="UTC").normalize()
    else:
        day = __import__("pandas").Timestamp(datetime.now(timezone.utc).date(), tz="UTC")
    row = df[df["date"] == day]
    if row.empty:
        # use last available <= day
        row = df[df["date"] <= day].tail(1)
    if row.empty:
        print(json.dumps({"ok": False, "error": "no regime rows"}))
        return 1
    r = row.iloc[0]
    decision = decide(args.mode, str(r["regime"]), int(r["dwell"]))
    out = {
        "ok": True,
        "as_of": str(r["date"].date()),
        "regime": str(r["regime"]),
        "sideways_dwell": int(r["dwell"]),
        "mode": args.mode,
        **decision,
        "base_slug": BASE_SLUG,
        "early_slug": EARLY_SLUG,
        "live_policy_c": "unchanged",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
