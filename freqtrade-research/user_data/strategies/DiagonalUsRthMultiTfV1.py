# pragma pylint: disable=missing-docstring, invalid-name
"""빗각 US-RTH Multi-TF — 4h rails, 15m entries, US cash session (BTC).

UsOpen (09:30–12:30 NY) was too tight: 0–4 trades / 2w windows.
User intent: Inbum-style “when US market is open”, ~1 trade / 2 days OK.

Hypothesis: Multi-TF Mode A only during full US RTH (09:30–16:00 NY)
+ 15m vol >= SMA20 improves PF vs 24/7 Multi-TF.

Falsify if ≥2/3 windows: PF<1 or net<0.
Prefer ~30d windows (sparse by design).
Not CORE / LIVE.
"""
from __future__ import annotations

from datetime import time

import pandas as pd
from pandas import DataFrame

from DiagonalMultiTfDayV1 import DiagonalMultiTfDayV1


class DiagonalUsRthMultiTfV1(DiagonalMultiTfDayV1):
    us_tz = "America/New_York"
    us_start = time(9, 30)
    us_end = time(16, 0)  # full regular trading hours
    entry_vol_k = 1.0  # at least average 15m volume

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_indicators(dataframe, metadata)
        dataframe["vol_sma20"] = dataframe["volume"].rolling(20).mean()
        dataframe["vol_ok"] = dataframe["volume"] >= (
            self.entry_vol_k * dataframe["vol_sma20"]
        )
        dataframe["us_rth"] = self._us_rth_mask(dataframe["date"])
        return dataframe

    @staticmethod
    def _us_rth_mask(dates: pd.Series) -> pd.Series:
        d = pd.to_datetime(dates, utc=True)
        ny = d.dt.tz_convert("America/New_York")
        t = ny.dt.time
        wd = ny.dt.weekday < 5
        return wd & (t >= time(9, 30)) & (t < time(16, 0))

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
            & dataframe["us_rth"]
            & dataframe["vol_ok"]
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[
            (
                base
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
                & (dataframe["ch_slope"] < 0)
                & near_upper
                & (dataframe["close"] < dataframe["open"])
                & (dataframe["close"] < dataframe["ch_upper"])
            ),
            "enter_short",
        ] = 1
        return dataframe


if __name__ == "__main__":
    idx = pd.DatetimeIndex(
        [
            "2026-06-01 13:30:00+00:00",  # 09:30 EDT in
            "2026-06-01 19:45:00+00:00",  # 15:45 EDT in
            "2026-06-01 20:15:00+00:00",  # 16:15 EDT out
            "2026-06-06 15:00:00+00:00",  # Sat out
        ]
    )
    m = DiagonalUsRthMultiTfV1._us_rth_mask(pd.Series(idx))
    assert bool(m.iloc[0]) and bool(m.iloc[1])
    assert not bool(m.iloc[2]) and not bool(m.iloc[3])
    print("DiagonalUsRthMultiTfV1 self-check OK")
