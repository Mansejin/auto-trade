# pragma pylint: disable=missing-docstring, invalid-name
"""빗각 V2 day — volume-pivot channel Mode B failed-break retest (BTC 15m).

V1 Mode A (first-touch rail) falsified 2/3 windows.
Hypothesis: Discretionary 빗각 waits for a *failed* rail break, then enters
on reclaim in channel trend direction (not the first touch).

Long:  rising channel, close was < lower within 3 bars, crossed back above, green
Short: falling channel, close was > upper within 3 bars, crossed back below, red
Same anchors / liquidity gate / exits as V1 (do not retune V1 hypers).

Falsify if ≥2/3 windows: PF<1 or net return<0.
Not CORE / LIVE.
"""
from __future__ import annotations

from pandas import DataFrame

from technical import qtpylib

from DiagonalVolumePivotDayV1 import DiagonalVolumePivotDayV1


class DiagonalVolumePivotBreakRetestDayV2(DiagonalVolumePivotDayV1):
    # Inherit timeframe, pivots, liq gate, ROI/SL, exits from V1.
    fail_lookback = 3  # frozen with this version

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = self.fail_lookback
        below_lower_n = (
            (dataframe["close"] < dataframe["ch_lower"])
            .rolling(n)
            .max()
            .fillna(0)
            .astype(bool)
        )
        above_upper_n = (
            (dataframe["close"] > dataframe["ch_upper"])
            .rolling(n)
            .max()
            .fillna(0)
            .astype(bool)
        )
        base = (
            dataframe["ch_valid"]
            & dataframe["day_liquid"]
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[
            (
                base
                & (dataframe["ch_slope"] > 0)
                & below_lower_n
                & qtpylib.crossed_above(dataframe["close"], dataframe["ch_lower"])
                & (dataframe["close"] > dataframe["open"])
            ),
            "enter_long",
        ] = 1

        dataframe.loc[
            (
                base
                & (dataframe["ch_slope"] < 0)
                & above_upper_n
                & qtpylib.crossed_below(dataframe["close"], dataframe["ch_upper"])
                & (dataframe["close"] < dataframe["open"])
            ),
            "enter_short",
        ] = 1
        return dataframe
