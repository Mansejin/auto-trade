# pragma pylint: disable=missing-docstring, invalid-name
"""Visual 5m bear short SCALP v2 — denser signals (Bitget ETH).

v1 (EMA9 cross) only ~10 signals/day. User wants activity closer to
'every few 5m bars' for visual observation.

Hypothesis (observation only): In soft 5m bear (EMA21<EMA55), each bearish
candle that closes below EMA21 is a short micro-scalp.

Entry (short only):
  EMA21 < EMA55
  AND close < open          (bearish candle)
  AND close < EMA21
  AND RSI < 55
Exit: ROI +0.20% / SL -0.12%

Fee 0.06%x2 will dominate — paper/visual only. Not for funded SCALP sleeve.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta


class Visual5mBearShortV2(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 80

    stoploss = -0.0012
    minimal_roi = {"0": 0.002}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema21"] < dataframe["ema55"])
                & (dataframe["close"] < dataframe["open"])
                & (dataframe["close"] < dataframe["ema21"])
                & (dataframe["rsi"] < 55)
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
