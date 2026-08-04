# pragma pylint: disable=missing-docstring, invalid-name
"""빗각 Human-Soft day — forgive like a discretionary trader (BTC 15m).

Prior auto encodings (V1/V2/V1-gate) were rigid: every rail match entered.
Humans 용인(forgive): ignore one wick pierce, skip ugly angles/widths,
don't spam every touch.

Hypothesis: soft pierce + quality skip + cooldown raises expectancy vs V1
while keeping ~1–3 trades/day on liquid BTC.

Frozen (do not retune after seeing results):
  pierce_tol 0.40%   — wick beyond rail still "touch" if close back inside
  width      0.5–2.5% of mid — skip knife / dead flat channels
  slope_max  0.12%/bar — skip near-vertical "angles"
  cooldown   4 bars (1h) between new entries
  SL -0.8% / ROI +1.2% — wider than V1 hair-trigger

Same volume-pivot rails + day liquidity as V1.
Falsify if ≥2/3 windows: PF<1 or net<0.
Not CORE / LIVE.
"""
from __future__ import annotations

import numpy as np
from pandas import DataFrame

from DiagonalVolumePivotDayV1 import DiagonalVolumePivotDayV1


class DiagonalHumanSoftDayV1(DiagonalVolumePivotDayV1):
    stoploss = -0.008
    minimal_roi = {"0": 0.012}

    # Soft / human-like (frozen with this version letter)
    pierce_tol = 0.004
    width_min = 0.005
    width_max = 0.025
    slope_max_per_bar = 0.0012  # |Δprice/mid| per bar
    cooldown_bars = 4

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_indicators(dataframe, metadata)
        mid = dataframe["ch_mid"].replace(0, np.nan)
        width = (dataframe["ch_upper"] - dataframe["ch_lower"]) / mid
        # slope is absolute price per bar; normalize by mid
        slope_pct = dataframe["ch_slope"].abs() / mid

        dataframe["ch_quality"] = (
            dataframe["ch_valid"]
            & width.between(self.width_min, self.width_max)
            & (slope_pct <= self.slope_max_per_bar)
        )

        # Soft touch zone: low/high may pierce by pierce_tol, close must reclaim
        tol = self.pierce_tol
        dataframe["soft_long_zone"] = (
            (dataframe["low"] <= dataframe["ch_lower"] * (1 + tol))
            & (dataframe["close"] >= dataframe["ch_lower"] * (1 - tol))
            & (dataframe["close"] > dataframe["ch_lower"])
        )
        dataframe["soft_short_zone"] = (
            (dataframe["high"] >= dataframe["ch_upper"] * (1 - tol))
            & (dataframe["close"] <= dataframe["ch_upper"] * (1 + tol))
            & (dataframe["close"] < dataframe["ch_upper"])
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        base = (
            dataframe["ch_quality"]
            & dataframe["day_liquid"]
            & (dataframe["volume"] > 0)
        )

        raw_long = (
            base
            & (dataframe["ch_slope"] > 0)
            & dataframe["soft_long_zone"]
            & (dataframe["close"] > dataframe["open"])
        )
        raw_short = (
            base
            & (dataframe["ch_slope"] < 0)
            & dataframe["soft_short_zone"]
            & (dataframe["close"] < dataframe["open"])
        )

        # Cooldown: suppress signals within N bars of a prior raw signal
        enter_long = self._apply_cooldown(raw_long.to_numpy(dtype=bool))
        enter_short = self._apply_cooldown(raw_short.to_numpy(dtype=bool))
        # If both fire same bar, skip (human wouldn't flip-flop)
        both = enter_long & enter_short
        enter_long = enter_long & ~both
        enter_short = enter_short & ~both

        dataframe.loc[enter_long, "enter_long"] = 1
        dataframe.loc[enter_short, "enter_short"] = 1
        return dataframe

    def _apply_cooldown(self, raw: np.ndarray) -> np.ndarray:
        out = np.zeros(len(raw), dtype=bool)
        last = -10**9
        cd = self.cooldown_bars
        for i, hit in enumerate(raw):
            if hit and (i - last) >= cd:
                out[i] = True
                last = i
        return out

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Soft exit: mid still OK; also allow exit if close clearly outside opposite
        # rail beyond pierce (channel thesis broken) — human cuts when thesis dies
        tol = self.pierce_tol
        dataframe.loc[
            dataframe["ch_valid"]
            & (
                (dataframe["close"] >= dataframe["ch_mid"])
                | (dataframe["close"] < dataframe["ch_lower"] * (1 - tol))
            ),
            "exit_long",
        ] = 1
        dataframe.loc[
            dataframe["ch_valid"]
            & (
                (dataframe["close"] <= dataframe["ch_mid"])
                | (dataframe["close"] > dataframe["ch_upper"] * (1 + tol))
            ),
            "exit_short",
        ] = 1
        return dataframe
