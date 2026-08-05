# pragma pylint: disable=missing-docstring, invalid-name
"""Bitget BTCUSDT-M 5m RSI+Ichimoku SHORT v3 — true futures redesign.

Search knobs (class attrs; patched by scripts/_search_rsi_ichi_short_v3_ft.py):
  rsi_thr, entry_mode ('fade_not_above'|'fade_below'|'level_below'),
  adx_mode ('off'|'lt30'|'gte25'), stoploss, minimal_roi

Exit: SL/ROI only (no indicator exit) to avoid same-bar entry/exit conflict.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta


class RsiIchiScalpShortV3(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 80

    stoploss = -0.003
    minimal_roi = {"0": 0.008}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    # Best non-hit vs PF>=1.2 both halves (h1≈1.10 n19 / h2≈0.99 n32). Research only.
    rsi_thr = 68
    entry_mode = "fade_not_above"  # fade_not_above | fade_below | level_below
    adx_mode = "off"  # off | lt30 | gte25

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
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
        dataframe["below_cloud"] = (dataframe["close"] < dataframe["cloud1"]) & (
            dataframe["close"] < dataframe["cloud2"]
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        thr = self.rsi_thr
        mode = self.entry_mode
        adx_m = self.adx_mode

        if mode == "fade_not_above":
            base = (dataframe["rsi_prev"] > thr) & (dataframe["rsi"] < thr) & (
                ~dataframe["above_cloud"].fillna(True)
            )
        elif mode == "fade_below":
            base = (dataframe["rsi_prev"] > thr) & (dataframe["rsi"] < thr) & (
                dataframe["below_cloud"].fillna(False)
            )
        else:  # level_below
            base = (dataframe["rsi"] > thr) & dataframe["below_cloud"].fillna(False)

        if adx_m == "lt30":
            base = base & (dataframe["adx"] < 30)
        elif adx_m == "gte25":
            base = base & (dataframe["adx"] >= 25)

        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe.loc[
            base
            & dataframe["cloud1"].notna()
            & (dataframe["volume"] > 0),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
