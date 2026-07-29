# pragma pylint: disable=missing-docstring, invalid-name
"""StochRSI range MR + ADX switch, long+short (Bitget research).

Long:  ADX<20, StochRSI K cross_above D, K<30, close<bb_mid
Short: ADX<20, StochRSI K cross_below D, K>70, close>bb_mid
Exit:  K extreme / mid reclaim / ADX>=25
"""
from __future__ import annotations

from pandas import DataFrame
from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class StochRsiBbMidAdxSwitchV3(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1h"
    startup_candle_count = 40
    stoploss = -0.02
    minimal_roi = {"0": 0.035}
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        stoch = ta.STOCHRSI(dataframe, timeperiod=14, fastk_period=3, fastd_period=3)
        # pandas-ta / talib STOCHRSI returns fastk/fastd
        if isinstance(stoch, DataFrame):
            dataframe["srsi_k"] = stoch["fastk"]
            dataframe["srsi_d"] = stoch["fastd"]
        else:
            dataframe["srsi_k"] = stoch
            dataframe["srsi_d"] = ta.SMA(dataframe["srsi_k"], timeperiod=3)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lower"] = bb["lower"]
        dataframe["bb_mid"] = bb["mid"]
        dataframe["bb_upper"] = bb["upper"]
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["adx"] < 20)
                & (qtpylib.crossed_above(dataframe["srsi_k"], dataframe["srsi_d"]))
                & (dataframe["srsi_k"] < 30)
                & (dataframe["close"] < dataframe["bb_mid"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        dataframe.loc[
            (
                (dataframe["adx"] < 20)
                & (qtpylib.crossed_below(dataframe["srsi_k"], dataframe["srsi_d"]))
                & (dataframe["srsi_k"] > 70)
                & (dataframe["close"] > dataframe["bb_mid"])
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["srsi_k"] > 70)
                | (dataframe["close"] >= dataframe["bb_mid"])
                | (dataframe["adx"] >= 25)
            ),
            "exit_long",
        ] = 1
        dataframe.loc[
            (
                (dataframe["srsi_k"] < 30)
                | (dataframe["close"] <= dataframe["bb_mid"])
                | (dataframe["adx"] >= 25)
            ),
            "exit_short",
        ] = 1
        return dataframe
