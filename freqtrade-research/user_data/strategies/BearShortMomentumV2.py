# pragma pylint: disable=missing-docstring, invalid-name
"""Bear-regime short scalp v2 — Bitget BTCUSDT-M (research).

v1 (RSI>70 + BB upper fade) produced 0 trades on Nov-2025 bear window —
oversold-bounce-into-70 is too rare while -DI already dominates. Abandoned.

Hypothesis (v2): In a daily bear tape, 5m pullbacks that lose EMA20 while
bearish DI and ADX remain active resume the downtrend. Short the reclaim failure.

Entry (short only):
  ADX(14) >= 25
  AND -DI > +DI
  AND close < EMA(20)
  AND RSI(14) crossed below 50
Exit:
  ROI +0.8% / SL -0.35%
  OR RSI > 55 OR close > EMA(20) OR ADX < 18

Fee: Bitget taker 0.06%. Do not retune after scoring.
Do not change Upbit Policy C bear map without human approve.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class BearShortMomentumV2(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 40

    stoploss = -0.0035
    minimal_roi = {"0": 0.008}
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
                (dataframe["adx"] >= 25)
                & (dataframe["minus_di"] > dataframe["plus_di"])
                & (dataframe["close"] < dataframe["ema20"])
                & (qtpylib.crossed_below(dataframe["rsi"], 50))
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] > 55)
                | (dataframe["close"] > dataframe["ema20"])
                | (dataframe["adx"] < 18)
            ),
            "exit_short",
        ] = 1
        dataframe["exit_long"] = 0
        return dataframe
