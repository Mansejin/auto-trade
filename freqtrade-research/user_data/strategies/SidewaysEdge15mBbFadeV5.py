# pragma pylint: disable=missing-docstring, invalid-name
"""LIVE SCALP — Bitget port of strategies/daytrade-edge-side-15m-bb-fade-v5.json

Long-only: ADX<20 + RSI<30 + close<=BB lower → exit BB upper.
SL 0.8% / ROI 2.5%. Fee 0.06%.
Sideways regime only — must be OFF in bull.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class SidewaysEdge15mBbFadeV5(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "15m"
    startup_candle_count = 40

    stoploss = -0.008
    minimal_roi = {"0": 0.025}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lower"] = bb["lower"]
        dataframe["bb_mid"] = bb["mid"]
        dataframe["bb_upper"] = bb["upper"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["adx"] < 20)
                & (dataframe["rsi"] < 30)
                & (dataframe["close"] <= dataframe["bb_lower"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] >= dataframe["bb_upper"]),
            "exit_long",
        ] = 1
        dataframe["exit_short"] = 0
        return dataframe
