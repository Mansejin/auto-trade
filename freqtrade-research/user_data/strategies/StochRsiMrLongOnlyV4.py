# pragma pylint: disable=missing-docstring, invalid-name
"""Long-only StochRSI MR + ADX switch (Bitget). Shorts disabled after FT shorts dragged SW2."""
from __future__ import annotations

from pandas import DataFrame
from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class StochRsiMrLongOnlyV4(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "1h"
    startup_candle_count = 40
    stoploss = -0.025
    minimal_roi = {"0": 0.04}
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        stoch = ta.STOCHRSI(dataframe, timeperiod=14, fastk_period=3, fastd_period=3)
        if isinstance(stoch, DataFrame):
            dataframe["srsi_k"] = stoch["fastk"]
            dataframe["srsi_d"] = stoch["fastd"]
        else:
            dataframe["srsi_k"] = stoch
            dataframe["srsi_d"] = ta.SMA(dataframe["srsi_k"], timeperiod=3)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_mid"] = bb["mid"]
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["adx"] < 20)
                & (qtpylib.crossed_above(dataframe["srsi_k"], dataframe["srsi_d"]))
                & (dataframe["srsi_k"] < 30)
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] >= dataframe["bb_mid"])
                | (dataframe["adx"] >= 25)
            ),
            "exit_long",
        ] = 1
        return dataframe
