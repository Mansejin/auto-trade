# pragma pylint: disable=missing-docstring, invalid-name
"""나씨 3틱 A — 상태머신 틱 카운트 + 1/40 DCA.

Card: docs/research/nassi-3tick-a-statemachine-card-frozen.md
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

from nassi_tick_count import three_tick_entries


class NassiThreeTickLongDcaA1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "5m"
    startup_candle_count = 40

    body_k = 1.5
    add_step_pct = 0.004
    max_adds = 5

    body_lookback = 20
    short_frac = 0.5
    sideways_reset = 3
    stake_slices = 40
    min_run_pct = 0.003
    pump_k = 3.0
    pump_lookback = 6

    position_adjustment_enable = True
    max_entry_position_adjustment = 5

    stoploss = -0.20
    use_custom_stoploss = False
    minimal_roi = {"0": 100}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        o, c = dataframe["open"], dataframe["close"]
        body = (c - o).abs()
        med = body.rolling(self.body_lookback).median()
        enter, counts = three_tick_entries(
            o,
            c,
            body_k=self.body_k,
            lookback=self.body_lookback,
            short_frac=self.short_frac,
            sideways_reset=self.sideways_reset,
        )
        # run drop over last 3 bars (approx when signal fires)
        run_drop = (o.shift(2) - c) / c.clip(lower=1e-12)
        big_green = (c > o) & (body >= self.pump_k * med)
        recent_pump = big_green.rolling(self.pump_lookback).max().fillna(0).astype(bool)

        dataframe["tick_count"] = counts
        dataframe["enter_3tick"] = (
            enter & (run_drop >= self.min_run_pct) & ~recent_pump
        ).fillna(False)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["enter_3tick"] & (dataframe["volume"] > 0),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: float | None,
        max_stake: float,
        leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        stake = proposed_stake / self.stake_slices
        if min_stake is not None:
            stake = max(stake, min_stake)
        return min(stake, max_stake)

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
        adverse = (trade.open_rate - current_rate) / trade.open_rate
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
        if current_profit >= 0.001:
            return "avg_reclaim"
        return None


if __name__ == "__main__":
    # quiet then 3 meaningful reds → enter on 3rd
    o = np.full(30, 100.0)
    c = np.full(30, 100.05)
    for i in range(20):
        o[i], c[i] = 100.0, 100.05
    for i, (oo, cc) in enumerate([(100.0, 99.7), (99.7, 99.4), (99.4, 99.1)], start=20):
        o[i], c[i] = oo, cc
    enter, counts = three_tick_entries(pd.Series(o), pd.Series(c))
    assert bool(enter.iloc[22]) and int(counts.iloc[22]) == 3

    # insert tiny red between ticks → should NOT count as tick; need 3 real ones
    o2, c2 = o.copy(), c.copy()
    o2[21], c2[21] = 99.7, 99.69  # tiny red (non-meaningful)
    enter2, _ = three_tick_entries(pd.Series(o2), pd.Series(c2))
    assert not bool(enter2.iloc[22])

    print("NassiThreeTickLongDcaA1 self-check OK")
