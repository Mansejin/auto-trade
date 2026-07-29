# pragma pylint: disable=missing-docstring, invalid-name
"""Bear short SCALP sleeve v8 — 1h DI continuation (Bitget BTCUSDT-M).

Wider TF / wider R:R vs 5m–15m fee grind. Hypothesis: when 1h structure is
already bear (EMA50<EMA200) and -DI crosses above +DI with ADX>=25, short
continuation until DI flips or price reclaims EMA50.

Entry (short only):
  EMA50 < EMA200
  AND -DI crossed_above +DI
  AND ADX >= 25
  AND close < EMA50
Exit:
  ROI +2.5% / SL -1.2%
  OR +DI > -DI OR close > EMA50 OR ADX < 18

Fee 0.06%. SCALP sleeve only.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class BearShortDiContinuationV8(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1h"
    startup_candle_count = 220

    stoploss = -0.012
    minimal_roi = {"0": 0.025}
    trailing_stop = False
    use_exit_signal = True
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
                & (qtpylib.crossed_above(dataframe["minus_di"], dataframe["plus_di"]))
                & (dataframe["adx"] >= 25)
                & (dataframe["close"] < dataframe["ema50"])
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["plus_di"] > dataframe["minus_di"])
                | (dataframe["close"] > dataframe["ema50"])
                | (dataframe["adx"] < 18)
            ),
            "exit_short",
        ] = 1
        dataframe["exit_long"] = 0
        return dataframe
