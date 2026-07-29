# pragma pylint: disable=missing-docstring, invalid-name
"""나씨 3-bar fade + DCA (순환매매) — fade then average into reclaim.

Card: docs/research/nassi-3bar-fade-dca-card-frozen.md
Hypers (frozen): body_k=1.5, add_step_pct=0.004, max_adds=2

BTC 5m 24h. Exit at avg+buffer. Hard floor -20% only.
Falsify if ≥2/3 ~30d: PF<1 or net<0.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy


class NassiThreeBarFadeDcaV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 40

    # --- frozen hypers (≤3) ---
    body_k = 1.5
    add_step_pct = 0.004
    max_adds = 2

    body_lookback = 20  # constant

    position_adjustment_enable = True
    max_entry_position_adjustment = 2  # == max_adds

    stoploss = -0.20  # research blast-radius floor only
    use_custom_stoploss = False
    minimal_roi = {"0": 100}  # disable ROI; custom_exit handles reclaim
    trailing_stop = False
    # custom_exit only runs when use_exit_signal is True (freqtrade should_exit)
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        o = dataframe["open"]
        c = dataframe["close"]
        body = (c - o).abs()
        med = body.rolling(self.body_lookback).median()
        long_bar = body >= self.body_k * med
        green = c > o
        red = c < o

        dataframe["fade_short"] = (
            long_bar
            & long_bar.shift(1)
            & long_bar.shift(2)
            & green
            & green.shift(1)
            & green.shift(2)
        ).fillna(False)
        dataframe["fade_long"] = (
            long_bar
            & long_bar.shift(1)
            & long_bar.shift(2)
            & red
            & red.shift(1)
            & red.shift(2)
        ).fillna(False)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["fade_long"] & (dataframe["volume"] > 0),
            "enter_long",
        ] = 1
        dataframe.loc[
            dataframe["fade_short"] & (dataframe["volume"] > 0),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe

    def adjust_trade_position(
        self,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        min_stake: float | None,
        max_stake: float,
        current_entry_rate: float,
        current_exit_rate: float,
        current_entry_profit: float,
        current_exit_profit: float,
        **kwargs,
    ) -> float | None:
        filled = trade.nr_of_successful_entries
        if filled >= 1 + self.max_adds:
            return None
        if trade.open_rate <= 0:
            return None
        if trade.is_short:
            adverse = (current_rate - trade.open_rate) / trade.open_rate
        else:
            adverse = (trade.open_rate - current_rate) / trade.open_rate
        # need another full step beyond current entry count
        if adverse < self.add_step_pct * filled:
            return None
        slice_stake = trade.stake_amount / filled
        if min_stake is not None and slice_stake < min_stake:
            slice_stake = min_stake
        if slice_stake > max_stake:
            return None
        return slice_stake

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> str | bool | None:
        # 평단 도달/소폭 상회 (fee buffer)
        if current_profit >= 0.001:
            return "avg_reclaim"
        return None


if __name__ == "__main__":
    body_k, lookback = 1.5, 20
    o = np.full(25, 100.0)
    c = np.full(25, 100.05)
    for i, (oo, cc) in enumerate([(100.0, 100.4), (100.4, 100.8), (100.8, 101.2)], start=20):
        o[i], c[i] = oo, cc
    body = np.abs(c - o)
    med = pd.Series(body).rolling(lookback).median().to_numpy()
    long_bar = body >= body_k * med
    green = c > o
    bull = long_bar & np.roll(long_bar, 1) & np.roll(long_bar, 2) & green & np.roll(green, 1) & np.roll(green, 2)
    bull[:2] = False
    assert bool(bull[22])
    print("NassiThreeBarFadeDcaV1 self-check OK")
