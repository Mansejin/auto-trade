# pragma pylint: disable=missing-docstring, invalid-name
"""나씨 5분봉 3틱 롱 + 1/40 순환 DCA.

Card: docs/research/nassi-3tick-long-dca-card-frozen.md
Hypers (frozen): body_k=1.5, add_step_pct=0.004, max_adds=5

Long only. Exit avg+0.1%. Hard floor -20%.
Falsify if ≥2/3 ~30d: PF<1 or net<0.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy


class NassiThreeTickLongDcaV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "5m"
    startup_candle_count = 40

    # --- frozen hypers (≤3) ---
    body_k = 1.5
    add_step_pct = 0.004
    max_adds = 5

    # constants (not hypers)
    body_lookback = 20
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
        o = dataframe["open"]
        c = dataframe["close"]
        body = (c - o).abs()
        med = body.rolling(self.body_lookback).median()
        red = c < o
        green = c > o
        tick = red & (body >= self.body_k * med)

        run3 = tick & tick.shift(1) & tick.shift(2)
        run_drop = (o.shift(2) - c) / c.clip(lower=1e-12)
        run_ok = run_drop >= self.min_run_pct

        big_green = green & (body >= self.pump_k * med)
        recent_pump = big_green.rolling(self.pump_lookback).max().fillna(0).astype(bool)

        dataframe["enter_3tick"] = (run3 & run_ok & ~recent_pump).fillna(False)
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
        # 1/40 of what unlimited would stake this bar
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
    body_k, lookback = 1.5, 20
    o = np.full(30, 100.0)
    c = np.full(30, 100.05)  # tiny green / quiet
    for i in range(20):
        o[i], c[i] = 100.0, 100.05
    # 3 meaningful reds dropping ~0.5%+
    for i, (oo, cc) in enumerate([(100.0, 99.7), (99.7, 99.4), (99.4, 99.1)], start=20):
        o[i], c[i] = oo, cc
    body = np.abs(c - o)
    med = pd.Series(body).rolling(lookback).median().to_numpy()
    tick = (c < o) & (body >= body_k * med)
    run3 = tick & np.roll(tick, 1) & np.roll(tick, 2)
    run3[:2] = False
    assert bool(run3[22])
    print("NassiThreeTickLongDcaV1 self-check OK")
