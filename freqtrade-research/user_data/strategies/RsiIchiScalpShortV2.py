# pragma pylint: disable=missing-docstring, invalid-name
"""Bitget BTCUSDT-M 5m RSI+Ichimoku SHORT v2 (true futures).

Redesign after short-proxy invert was falsified on FT.

Entry (short only):
  RSI(14) fade across 68 (prev > 68 -> now < 68)
  AND price not fully above cloud (not (close > cloud1 AND close > cloud2))
  — avoids same-bar exit conflict that starved v1 fills.

Exit: ROI +0.8% / stoploss -0.3% only (no indicator exit).

Research only. Do not mount LIVE/Policy C from this alone.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta


class RsiIchiScalpShortV2(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 80

    stoploss = -0.004
    minimal_roi = {"0": 0.01}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    # tunable via hyperopt later; fixed for falsification pass
    rsi_thr = 65

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
        dataframe["above_cloud"] = (dataframe["close"] > dataframe["cloud1"]) & (
            dataframe["close"] > dataframe["cloud2"]
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        thr = self.rsi_thr
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe.loc[
            (
                (dataframe["rsi_prev"] > thr)
                & (dataframe["rsi"] < thr)
                & (~dataframe["above_cloud"].fillna(True))
                & dataframe["cloud1"].notna()
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
