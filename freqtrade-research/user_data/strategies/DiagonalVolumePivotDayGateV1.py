# pragma pylint: disable=missing-docstring, invalid-name
"""빗각 V1-gate — V1 Mode A + soft daily direction gate (BTC 15m).

V1 falsified: longs bled in down markets / shorts in up markets.
Hypothesis: same volume-pivot Mode A entries, but
  bull day  -> long only
  bear day  -> short only
  else      -> both (keep day-trade frequency on non-trend days)

Regime = Policy-C style on Binance BTC 1d (Bitget 1d too short for SMA200),
prior completed daily bar only. Soft else=(both) differs from scalp regime-gate
which flats sideways.

Falsify if ≥2/3 windows: PF<1 or net<0.
Not CORE / LIVE.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta

from DiagonalVolumePivotDayV1 import DiagonalVolumePivotDayV1


class DiagonalVolumePivotDayGateV1(DiagonalVolumePivotDayV1):
    _regime_by_date: dict | None = None

    def _load_regime_map(self) -> dict:
        if self._regime_by_date is not None:
            return self._regime_by_date

        root = Path(__file__).resolve().parents[1]  # user_data/
        path = root / "data" / "binance" / "futures" / "BTC_USDT_USDT-1d-futures.feather"
        if not path.exists():
            path = root / "data" / "futures" / "BTC_USDT_USDT-1d-futures.feather"
        if not path.exists():
            self._regime_by_date = {}
            return self._regime_by_date

        inf = pd.read_feather(path).sort_values("date").reset_index(drop=True)
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

        regime: dict = {}
        for i in range(len(inf) - 1):
            next_day = pd.Timestamp(inf.loc[i + 1, "date"]).floor("D")
            if bool(bull.iloc[i]):
                flags = (1, 0)
            elif bool(bear.iloc[i]):
                flags = (0, 1)
            else:
                flags = (1, 1)  # soft: sideways/transition keep both
            regime[next_day] = flags
        self._regime_by_date = regime
        return regime

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_indicators(dataframe, metadata)
        regime = self._load_regime_map()
        norm: dict = {}
        for k, v in regime.items():
            kk = pd.Timestamp(k)
            if kk.tzinfo is None:
                kk = kk.tz_localize("UTC")
            else:
                kk = kk.tz_convert("UTC")
            norm[kk.floor("D")] = v

        dates = pd.to_datetime(dataframe["date"], utc=True).dt.floor("D")
        # Missing map -> both allowed (do not silently flat the whole sample)
        dataframe["allow_long_1d"] = [norm.get(d, (1, 1))[0] for d in dates]
        dataframe["allow_short_1d"] = [norm.get(d, (1, 1))[1] for d in dates]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        tol = self.touch_pct
        near_lower = (
            (dataframe["low"] <= dataframe["ch_lower"] * (1 + tol))
            & (dataframe["close"] >= dataframe["ch_lower"] * (1 - tol))
        )
        near_upper = (
            (dataframe["high"] >= dataframe["ch_upper"] * (1 - tol))
            & (dataframe["close"] <= dataframe["ch_upper"] * (1 + tol))
        )
        base = (
            dataframe["ch_valid"]
            & dataframe["day_liquid"]
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[
            (
                base
                & (dataframe["allow_long_1d"] == 1)
                & (dataframe["ch_slope"] > 0)
                & near_lower
                & (dataframe["close"] > dataframe["open"])
                & (dataframe["close"] > dataframe["ch_lower"])
            ),
            "enter_long",
        ] = 1

        dataframe.loc[
            (
                base
                & (dataframe["allow_short_1d"] == 1)
                & (dataframe["ch_slope"] < 0)
                & near_upper
                & (dataframe["close"] < dataframe["open"])
                & (dataframe["close"] < dataframe["ch_upper"])
            ),
            "enter_short",
        ] = 1
        return dataframe
