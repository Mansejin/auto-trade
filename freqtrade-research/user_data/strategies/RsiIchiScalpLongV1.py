# pragma pylint: disable=missing-docstring, invalid-name
"""Bitget BTCUSDT-M 5m RSI+Ichimoku LONG only (true futures).

Entry: RSI rebound across 22. Exit: close below both cloud spans (shift 26).
SL -0.5% / ROI +2.0%. Research only.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta


class RsiIchiScalpLongV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "5m"
    startup_candle_count = 80

    stoploss = -0.005
    minimal_roi = {"0": 0.02}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        high, low = dataframe["high"], dataframe["low"]
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2.0
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2.0
        span1 = (tenkan + kijun) / 2.0
        span2 = (high.rolling(52).max() + low.rolling(52).min()) / 2.0
        dataframe["cloud1"] = span1.shift(26)
        dataframe["cloud2"] = span2.shift(26)
        dataframe["rsi_prev"] = dataframe["rsi"].shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe.loc[
            (
                (dataframe["rsi_prev"] < 22)
                & (dataframe["rsi"] > 22)
                & (dataframe["volume"] > 0)
                & dataframe["cloud1"].notna()
                & dataframe["cloud2"].notna()
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        below = (
            dataframe["cloud1"].notna()
            & dataframe["cloud2"].notna()
            & (dataframe["close"] < dataframe["cloud1"])
            & (dataframe["close"] < dataframe["cloud2"])
        )
        dataframe.loc[below, "exit_long"] = 1
        return dataframe
