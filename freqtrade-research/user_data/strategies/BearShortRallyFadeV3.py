# pragma pylint: disable=missing-docstring, invalid-name
"""Bear-regime short scalp v3 — Bitget BTCUSDT-M (research).

v1: RSI>70 + BB upper fade → 0 trades (too rare in bear).
v2: RSI cross below 50 + below EMA20 momentum → PF 0.24–0.78, WR 16–27%
    on 3 bear windows (falsified: late chase into bounces).

Hypothesis (v3): In daily bear, temporary 15m rallies (RSI>58 above EMA20)
while -DI still dominates are fadeable dead-cat pops. Short strength, not weakness.

Entry (short only):
  RSI(14) > 58
  AND close > EMA(20)
  AND ADX(14) >= 22
  AND -DI > +DI
Exit:
  ROI +1.2% / SL -0.5%
  OR RSI < 42 OR close < EMA(20) OR ADX < 16

Fee: 0.06% taker. No retune after scoring. No Policy C change without approve.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta


class BearShortRallyFadeV3(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 40

    stoploss = -0.005
    minimal_roi = {"0": 0.012}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] > 58)
                & (dataframe["close"] > dataframe["ema20"])
                & (dataframe["adx"] >= 22)
                & (dataframe["minus_di"] > dataframe["plus_di"])
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] < 42)
                | (dataframe["close"] < dataframe["ema20"])
                | (dataframe["adx"] < 16)
            ),
            "exit_short",
        ] = 1
        dataframe["exit_long"] = 0
        return dataframe
