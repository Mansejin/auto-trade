# pragma pylint: disable=missing-docstring, invalid-name
"""Bitget BTC short v4 — post v3 miss: no-cloud fade OR cloud-break entry."""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta


class RsiIchiScalpShortV4(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 80

    stoploss = -0.003
    minimal_roi = {"0": 0.008}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    rsi_thr = 68
    entry_mode = "fade_plain"  # fade_plain | cloud_break

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        high, low = dataframe["high"], dataframe["low"]
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2.0
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2.0
        span1 = (tenkan + kijun) / 2.0
        span2 = (high.rolling(52).max() + low.rolling(52).min()) / 2.0
        dataframe["cloud1"] = span1.shift(26)
        dataframe["cloud2"] = span2.shift(26)
        dataframe["cloud_top"] = dataframe[["cloud1", "cloud2"]].max(axis=1)
        dataframe["cloud_bot"] = dataframe[["cloud1", "cloud2"]].min(axis=1)
        dataframe["rsi_prev"] = dataframe["rsi"].shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        thr = self.rsi_thr
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        if self.entry_mode == "fade_plain":
            cond = (dataframe["rsi_prev"] > thr) & (dataframe["rsi"] < thr)
        else:
            # close was >= cloud_top, now < cloud_bot (full break below cloud)
            cond = (
                (dataframe["close"].shift(1) >= dataframe["cloud_top"].shift(1))
                & (dataframe["close"] < dataframe["cloud_bot"])
                & (dataframe["rsi"] > thr)
            )
        dataframe.loc[
            cond & (dataframe["volume"] > 0) & dataframe["cloud1"].notna(),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
