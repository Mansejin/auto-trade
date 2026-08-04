# pragma pylint: disable=missing-docstring, invalid-name
"""cal-event-sweep-fade-r3-v1 — dry-run research only.

Holdout survived narrowly; train failed → LIVE arming disabled via ALLOW_LIVE.
See docs/research/cal-event-sweep-fade-r3-v1.md.
"""
from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from pandas import DataFrame
import pandas as pd
import numpy as np

from freqtrade.strategy import IStrategy
import talib.abstract as ta


class CalEventSweepFadeR3V1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 220
    stoploss = -0.005
    minimal_roi = {"0": 0.015}
    use_exit_signal = False
    process_only_new_candles = True

    # Train failed — refuse LIVE even if someone points a live config here
    ALLOW_LIVE = False

    ATR_K = 2.0
    RECLAIM_BARS = 4
    _events: list[dict] | None = None
    _regime_by_day: dict | None = None

    def bot_start(self, **kwargs) -> None:
        if not self.config.get("dry_run", True) and not self.ALLOW_LIVE:
            raise RuntimeError(
                "CalEventSweepFadeR3V1: LIVE blocked (train PF<1). dry_run only."
            )

    def _load_events(self) -> list[dict]:
        if self._events is not None:
            return self._events
        root = Path(__file__).resolve().parents[3]  # repo root from user_data/strategies
        path = root / "config" / "us-macro-calendar.json"
        if not path.exists():
            path = Path(__file__).resolve().parents[1] / "us-macro-calendar.json"
        self._events = json.loads(path.read_text(encoding="utf-8"))["events"]
        return self._events

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        # daily regime from resampled 15m (prior day)
        tmp = dataframe.set_index("date")
        d1 = (
            tmp.resample("1D")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
            .dropna()
        )
        d1["sma50"] = d1["close"].rolling(50).mean()
        d1["sma200"] = d1["close"].rolling(200).mean()
        d1["adx"] = ta.ADX(d1, timeperiod=14)
        d1["pdi"] = ta.PLUS_DI(d1, timeperiod=14)
        d1["mdi"] = ta.MINUS_DI(d1, timeperiod=14)
        sideways = d1["adx"] < 20
        bull = (
            (d1["close"] > d1["sma200"])
            & (d1["sma50"] > d1["sma200"])
            & (d1["pdi"] >= d1["mdi"])
            & (~sideways)
        )
        bear = (
            (d1["close"] < d1["sma200"])
            & (d1["sma50"] < d1["sma200"])
            & (d1["close"] < d1["sma50"])
            & (d1["mdi"] > d1["pdi"])
            & (~sideways)
        )
        reg = pd.Series("transition", index=d1.index)
        reg[sideways.fillna(False)] = "sideways"
        reg[bull.fillna(False)] = "bull"
        reg[bear.fillna(False)] = "bear"
        reg = reg.shift(1)
        day = pd.to_datetime(dataframe["date"], utc=True).dt.normalize()
        dataframe["regime"] = day.map(reg).fillna("warmup")

        # event window flags (vectorized approx for backtest)
        events = self._load_events()
        ev_ts = [pd.Timestamp(e["ts_utc"], tz="UTC") for e in events]
        dataframe["in_event"] = 0
        dataframe["box_hi"] = np.nan
        dataframe["box_lo"] = np.nan
        dataframe["vol_ok"] = 0
        # For backtest speed: mark bars within 24h of an event
        dates = pd.to_datetime(dataframe["date"], utc=True)
        for ts in ev_ts:
            mask = (dates >= ts) & (dates < ts + timedelta(hours=24))
            if not mask.any():
                continue
            dataframe.loc[mask, "in_event"] = 1
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Full sweep logic is in the offline study; here a simplified live gate:
        # only allow entries during in_event + regime — exact sweep detected in custom
        # via last bars. For safety while LIVE blocked, still compute signals for dry-run BT.
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        if len(dataframe) < 30:
            return dataframe

        events = self._load_events()
        dates = pd.to_datetime(dataframe["date"], utc=True)
        for ts in (pd.Timestamp(e["ts_utc"], tz="UTC") for e in events):
            wmask = (dates >= ts) & (dates < ts + timedelta(hours=24))
            widx = dataframe.index[wmask]
            if len(widx) < 12:
                continue
            hour_idx = widx[:4]
            rest_idx = widx[4:]
            hi0 = dataframe.loc[hour_idx, "high"].max()
            lo0 = dataframe.loc[hour_idx, "low"].min()
            atr0 = dataframe.loc[hour_idx[0], "atr"]
            # atr from bar before event
            pre_i = dataframe.index[dates < ts]
            if len(pre_i) == 0 or pd.isna(atr0):
                atr_ref = dataframe.loc[pre_i[-1], "atr"] if len(pre_i) else atr0
            else:
                atr_ref = dataframe.loc[pre_i[-1], "atr"]
            if pd.isna(atr_ref) or (hi0 - lo0) < self.ATR_K * float(atr_ref):
                continue
            fired = False
            for i, ix in enumerate(rest_idx):
                if fired:
                    break
                regime = dataframe.loc[ix, "regime"]
                row = dataframe.loc[ix]
                chunk = rest_idx[i : i + self.RECLAIM_BARS]
                if regime in ("bull", "transition") and float(row["low"]) < lo0:
                    for cx in chunk:
                        if float(dataframe.loc[cx, "close"]) >= lo0:
                            dataframe.loc[cx, "enter_long"] = 1
                            fired = True
                            break
                elif regime == "bear" and float(row["high"]) > hi0:
                    for cx in chunk:
                        if float(dataframe.loc[cx, "close"]) <= hi0:
                            dataframe.loc[cx, "enter_short"] = 1
                            fired = True
                            break
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
