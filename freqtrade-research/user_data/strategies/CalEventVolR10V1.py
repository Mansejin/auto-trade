# pragma pylint: disable=missing-docstring, invalid-name
"""cal-event-vol-reclaim-r10-v1 — RESEARCH STUB ONLY.

Event-study verdict: FALSIFIED (see docs/research/cal-event-vol-reclaim-r10-v1.md).
This strategy refuses all entries so it cannot be accidentally armed for LIVE.
Do not remove the hard block without a new surviving card id.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy


class CalEventVolR10V1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 40
    stoploss = -0.004
    minimal_roi = {"0": 0.04}
    process_only_new_candles = True

    # Hard block — falsified card
    CARD_FALSIFIED = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
