# pragma pylint: disable=missing-docstring, invalid-name
"""Bitget BTCUSDT-M 5m RSI+BB SHORT (true futures).

Entry: RSI > rsi_thr AND close > BB upper AND (optional ADX gate).
Exit: SL/ROI only.

Knobs patched by scripts/_search_rsi_bb_short_ft.py.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class RsiBbScalpShortV5(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 40

    stoploss = -0.003
    minimal_roi = {"0": 0.008}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    rsi_thr = 75
    bb_period = 20
    bb_std = 2.0
    adx_mode = "lt30"  # off | lt30 | gte25

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe),
            window=int(self.bb_period),
            stds=float(self.bb_std),
        )
        dataframe["bb_lower"] = bollinger["lower"]
        dataframe["bb_mid"] = bollinger["mid"]
        dataframe["bb_upper"] = bollinger["upper"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (dataframe["rsi"] > self.rsi_thr) & (
            dataframe["close"] > dataframe["bb_upper"]
        )
        if self.adx_mode == "lt30":
            cond = cond & (dataframe["adx"] < 30)
        elif self.adx_mode == "gte25":
            cond = cond & (dataframe["adx"] >= 25)

        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe.loc[cond & (dataframe["volume"] > 0), "enter_short"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
