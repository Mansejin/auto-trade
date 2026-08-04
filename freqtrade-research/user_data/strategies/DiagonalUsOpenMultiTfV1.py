# pragma pylint: disable=missing-docstring, invalid-name
"""빗각 US-open Multi-TF — 4h rails, 15m entries, US cash open only (BTC).

User note: Inbum traded around US market open; ~1 fill / 2 days is fine
if volume is there. Prior Multi-TF (24/7) was sparse *and* wrong hours.

Hypothesis: Same 4h→15m Mode A as DiagonalMultiTfDayV1, but only during
US RTH open window (09:30–12:30 America/New_York) AND 15m volume spike
beats unrestricted Multi-TF / V1.

Falsify if ≥2/3 windows: PF<1 or net<0.
Not CORE / LIVE.
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd
from pandas import DataFrame

from DiagonalMultiTfDayV1 import DiagonalMultiTfDayV1


class DiagonalUsOpenMultiTfV1(DiagonalMultiTfDayV1):
    # Frozen with this version — open window, not full RTH
    us_tz = "America/New_York"
    us_start = time(9, 30)
    us_end = time(12, 30)  # first ~3h after cash open
    entry_vol_k = 1.2  # 15m vol vs SMA20 at entry

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_indicators(dataframe, metadata)
        dataframe["vol_sma20"] = dataframe["volume"].rolling(20).mean()
        dataframe["vol_spike"] = dataframe["volume"] >= (
            self.entry_vol_k * dataframe["vol_sma20"]
        )
        dataframe["us_open"] = self._us_open_mask(dataframe["date"])
        return dataframe

    def _us_open_mask(self, dates: pd.Series) -> pd.Series:
        d = pd.to_datetime(dates, utc=True)
        ny = d.dt.tz_convert(self.us_tz)
        t = ny.dt.time
        # Weekdays only (Mon=0 .. Fri=4)
        wd = ny.dt.weekday < 5
        return wd & (t >= self.us_start) & (t < self.us_end)

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
            & dataframe["us_open"]
            & dataframe["vol_spike"]
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
    # ponytail: US open mask sanity (EDT Monday 10:00 NY = inside)
    idx = pd.DatetimeIndex(
        [
            "2026-06-01 13:30:00+00:00",  # 09:30 EDT
            "2026-06-01 16:00:00+00:00",  # 12:00 EDT
            "2026-06-01 17:00:00+00:00",  # 13:00 EDT — outside
            "2026-06-06 14:00:00+00:00",  # Saturday — outside
        ]
    )
    s = DiagonalUsOpenMultiTfV1()
    m = s._us_open_mask(pd.Series(idx))
    assert bool(m.iloc[0]) and bool(m.iloc[1])
    assert not bool(m.iloc[2]) and not bool(m.iloc[3])
    print("DiagonalUsOpenMultiTfV1 self-check OK")
