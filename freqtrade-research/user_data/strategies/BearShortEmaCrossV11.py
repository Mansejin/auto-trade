# pragma pylint: disable=missing-docstring, invalid-name
"""Bear short SCALP/단타 sleeve v11 — 4h trend continuation (Bitget).

Death-cross alone is too rare. Hypothesis: while 4h EMA50 < EMA200 and ADX>=25
with -DI>+DI, short when close crosses below EMA50 (pullback failure / resume).

Entry (short only):
  EMA50 < EMA200
  AND ADX >= 25
  AND -DI > +DI
  AND close crossed_below EMA50
Exit:
  ROI +4.0% / SL -2.0% only

Fee 0.06%. SCALP sleeve only.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class BearShortEmaCrossV11(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "4h"
    startup_candle_count = 220

    stoploss = -0.02
    minimal_roi = {"0": 0.04}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema50"] < dataframe["ema200"])
                & (dataframe["adx"] >= 25)
                & (dataframe["minus_di"] > dataframe["plus_di"])
                & (qtpylib.crossed_below(dataframe["close"], dataframe["ema50"]))
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
