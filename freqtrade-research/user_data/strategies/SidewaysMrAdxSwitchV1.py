# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
"""Sideways mean-reversion with ADX strength switch (Bitget research).

When ADX weak (<20): allow RSI+BB mean-reversion long AND short.
When ADX strong (>=25): no new MR entries (hand off to trend regime).
Exit MR also if ADX crosses to >=25 while in a trade (via custom exit).

Mirrors strategies/regime-sideways-mr-1h-adx-switch-v1.json idea on 1h futures.
Do not mount to LIVE / Policy C from this alone.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class SidewaysMrAdxSwitchV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1h"
    startup_candle_count = 40

    stoploss = -0.02
    minimal_roi = {"0": 0.03}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    # Frozen thresholds (do not hyperopt after seeing results)
    adx_entry_max = 20
    adx_switch = 25
    rsi_long = 35
    rsi_short = 65
    rsi_exit_long = 55
    rsi_exit_short = 45

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=20, stds=2
        )
        dataframe["bb_lower"] = bollinger["lower"]
        dataframe["bb_middle"] = bollinger["mid"]
        dataframe["bb_upper"] = bollinger["upper"]
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["mr_mode"] = (dataframe["adx"] < self.adx_entry_max).astype(int)
        dataframe["trend_switch"] = (dataframe["adx"] >= self.adx_switch).astype(int)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Only enter while sideways / weak ADX
        dataframe.loc[
            (
                (dataframe["mr_mode"] == 1)
                & (dataframe["rsi"] < self.rsi_long)
                & (dataframe["close"] <= dataframe["bb_lower"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1

        dataframe.loc[
            (
                (dataframe["mr_mode"] == 1)
                & (dataframe["rsi"] > self.rsi_short)
                & (dataframe["close"] >= dataframe["bb_upper"])
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Mean-reversion exits OR ADX strengthened -> switch off MR
        dataframe.loc[
            (
                (dataframe["rsi"] >= self.rsi_exit_long)
                | (dataframe["close"] >= dataframe["bb_middle"])
                | (dataframe["trend_switch"] == 1)
            ),
            "exit_long",
        ] = 1

        dataframe.loc[
            (
                (dataframe["rsi"] <= self.rsi_exit_short)
                | (dataframe["close"] <= dataframe["bb_middle"])
                | (dataframe["trend_switch"] == 1)
            ),
            "exit_short",
        ] = 1
        return dataframe
