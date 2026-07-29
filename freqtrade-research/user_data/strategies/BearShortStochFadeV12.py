# pragma pylint: disable=missing-docstring, invalid-name
"""Bear short SCALP sleeve v12 — 1h StochRSI overbought fade (Bitget).

Different indicator family vs EMA/Donchian/DI series. Hypothesis: in 1h bear
(EMA50<EMA200), StochRSI %K rolling over from >80 marks a shortable dead-cat.

Entry (short only):
  EMA50 < EMA200
  AND StochRSI fastk crossed_below 80
  AND ADX >= 20
Exit:
  ROI +1.5% / SL -0.8% only

Fee 0.06%. SCALP sleeve only.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class BearShortStochFadeV12(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1h"
    startup_candle_count = 220

    stoploss = -0.008
    minimal_roi = {"0": 0.015}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        stoch = ta.STOCHRSI(dataframe, timeperiod=14, fastk_period=3, fastd_period=3)
        dataframe["fastk"] = stoch["fastk"]
        dataframe["fastd"] = stoch["fastd"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema50"] < dataframe["ema200"])
                & (qtpylib.crossed_below(dataframe["fastk"], 80))
                & (dataframe["adx"] >= 20)
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
