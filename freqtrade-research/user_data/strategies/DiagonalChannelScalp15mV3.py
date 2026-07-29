# pragma pylint: disable=missing-docstring, invalid-name
"""빗각 단타 v3 — same channel logic on 15m (cleaner angle, still short-TF).

Hypothesis: 5m noise falsifies diagonal mean-reversion; 15m regression
channels are closer to hand-drawn 빗각 and still finish within hours.

Same entry/exit family as v1 but timeframe=15m, ROI +0.8% / SL -0.4%.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta


class DiagonalChannelScalp15mV3(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 60

    stoploss = -0.004
    minimal_roi = {"0": 0.008}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    lr_period = 30
    lr_stds = 2.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        p = self.lr_period
        dataframe["lr_mid"] = ta.LINEARREG(dataframe, timeperiod=p)
        dataframe["lr_slope"] = ta.LINEARREG_SLOPE(dataframe, timeperiod=p)
        resid = dataframe["close"] - dataframe["lr_mid"]
        dataframe["lr_std"] = resid.rolling(p).std()
        dataframe["lr_upper"] = dataframe["lr_mid"] + self.lr_stds * dataframe["lr_std"]
        dataframe["lr_lower"] = dataframe["lr_mid"] - self.lr_stds * dataframe["lr_std"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["lr_slope"] < 0)
                & (dataframe["close"] >= dataframe["lr_upper"])
                & (dataframe["close"] < dataframe["open"])
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        dataframe.loc[
            (
                (dataframe["lr_slope"] > 0)
                & (dataframe["close"] <= dataframe["lr_lower"])
                & (dataframe["close"] > dataframe["open"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] <= dataframe["lr_mid"]), "exit_short"] = 1
        dataframe.loc[(dataframe["close"] >= dataframe["lr_mid"]), "exit_long"] = 1
        return dataframe
