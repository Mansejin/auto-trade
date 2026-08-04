# pragma pylint: disable=missing-docstring, invalid-name
"""QQQ Mode B FROZEN — simple break → retest+reject, US RTH.

Card: docs/research/mode-b-rule-card-frozen.md
Hypers (frozen): vol_k=1.5, retest_bars=96, max_slope_pct=0.015

Hypothesis: continuation Mode B on QQQ US-RTH with rejection beats fees.
Falsify if ≥2/3 ~30d windows: PF<1 or net<0.
Not CORE / LIVE.
"""
from __future__ import annotations

from pandas import DataFrame
import pandas as pd

from technical import qtpylib

from DiagonalUsRthMultiTfV1 import DiagonalUsRthMultiTfV1


def _bool(s: pd.Series) -> pd.Series:
    return s.fillna(False).astype(bool)


class DiagonalQqqModeBFrozenV1(DiagonalUsRthMultiTfV1):
    # --- frozen hypers (≤3) ---
    vol_k = 1.5
    retest_bars = 96  # 15m × 96 ≈ 1 day
    max_slope_pct = 0.015

    use_exit_signal = False
    stoploss = -0.008
    minimal_roi = {"0": 0.01}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_indicators(dataframe, metadata)
        mid = dataframe["ch_mid"].replace(0, pd.NA)
        slope_pct = dataframe["ch_slope"].abs() / mid
        dataframe["slope_ok"] = _bool(slope_pct <= self.max_slope_pct)

        vol_ma = dataframe["volume"].rolling(20).mean()
        strong_vol = _bool(dataframe["volume"] >= (self.vol_k * vol_ma))
        valid = _bool(dataframe["ch_valid"]) & _bool(dataframe["slope_ok"])

        broke_up = _bool(
            qtpylib.crossed_above(dataframe["close"], dataframe["ch_upper"])
            & strong_vol
            & valid
        )
        broke_down = _bool(
            qtpylib.crossed_below(dataframe["close"], dataframe["ch_lower"])
            & strong_vol
            & valid
        )
        n = self.retest_bars
        dataframe["broke_up_recent"] = _bool(broke_up.rolling(n).max())
        dataframe["broke_down_recent"] = _bool(broke_down.rolling(n).max())
        dataframe["broke_up_now"] = broke_up
        dataframe["broke_down_now"] = broke_down
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        tol = self.touch_pct
        # Rejection required (S19): green/red candle at rail, not touch alone.
        retest_long = _bool(
            (dataframe["low"] <= dataframe["ch_upper"] * (1 + tol))
            & (dataframe["close"] >= dataframe["ch_upper"] * (1 - tol))
            & (dataframe["close"] <= dataframe["ch_upper"] * (1 + 2 * tol))
            & (dataframe["close"] > dataframe["open"])
        )
        retest_short = _bool(
            (dataframe["high"] >= dataframe["ch_lower"] * (1 - tol))
            & (dataframe["close"] <= dataframe["ch_lower"] * (1 + tol))
            & (dataframe["close"] >= dataframe["ch_lower"] * (1 - 2 * tol))
            & (dataframe["close"] < dataframe["open"])
        )

        long_cond = _bool(
            _bool(dataframe["ch_valid"])
            & _bool(dataframe["slope_ok"])
            & _bool(dataframe["us_rth"])
            & (dataframe["volume"] > 0)
            & _bool(dataframe["broke_up_recent"])
            & ~_bool(dataframe["broke_up_now"])
            & retest_long
        )
        short_cond = _bool(
            _bool(dataframe["ch_valid"])
            & _bool(dataframe["slope_ok"])
            & _bool(dataframe["us_rth"])
            & (dataframe["volume"] > 0)
            & _bool(dataframe["broke_down_recent"])
            & ~_bool(dataframe["broke_down_now"])
            & retest_short
        )
        both = long_cond & short_cond
        dataframe["enter_long"] = (long_cond & ~both).astype(int)
        dataframe["enter_short"] = (short_cond & ~both).astype(int)
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe


if __name__ == "__main__":
    assert DiagonalQqqModeBFrozenV1.vol_k == 1.5
    assert DiagonalQqqModeBFrozenV1.retest_bars == 96
    assert DiagonalQqqModeBFrozenV1.max_slope_pct == 0.015
    print("DiagonalQqqModeBFrozenV1 self-check OK")
