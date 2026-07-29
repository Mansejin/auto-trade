# pragma pylint: disable=missing-docstring, invalid-name
"""Visual 5m bear short SCALP — dense signals for observation (Bitget).

Goal: frequent 5m short activity so you can *see* the bot working — NOT a
fee-surviving edge. Expect PF < 1 after 0.06%×2 taker. Paper / research only.

Hypothesis (observation): In a soft bear tape (EMA21 < EMA55 on 5m), every
EMA9 cross below EMA21 is a shortable micro-impulse. Dense by design.

Entry (short only):
  EMA21 < EMA55
  AND close crossed_below EMA9
Exit: ROI +0.25% / SL -0.15% only (micro targets)

Do not promote to LIVE / SCALP funded sleeve without separate falsification.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class Visual5mBearShortV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 80

    stoploss = -0.0015
    minimal_roi = {"0": 0.0025}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema21"] < dataframe["ema55"])
                & (qtpylib.crossed_below(dataframe["close"], dataframe["ema9"]))
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
