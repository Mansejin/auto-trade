# pragma pylint: disable=missing-docstring, invalid-name
"""Bear-regime short scalp — Bitget BTCUSDT-M (research / optional LIVE later).

Hypothesis: In a daily bear tape, 5m oversold-bounces into RSI strength + BB upper
fade more often than they continue (dead-cat fade). Short only; no longs.

Entry (short):
  RSI(14) > 70 AND close > BB upper(20,2) AND ADX(14) >= 25 AND -DI > +DI
Exit:
  ROI +0.8% / stoploss -0.3% OR RSI < 45 OR close < BB middle OR ADX < 20

Fee assumption: Bitget taker 0.06%. Do not retune after seeing results.
Do not change Upbit Policy C bear map without human approve.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class BearShortScalpRsiBbV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 40

    stoploss = -0.003
    minimal_roi = {"0": 0.008}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lower"] = bb["lower"]
        dataframe["bb_mid"] = bb["mid"]
        dataframe["bb_upper"] = bb["upper"]
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Short-only scalp
        dataframe.loc[
            (
                (dataframe["rsi"] > 70)
                & (dataframe["close"] > dataframe["bb_upper"])
                & (dataframe["adx"] >= 25)
                & (dataframe["minus_di"] > dataframe["plus_di"])
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] < 45)
                | (dataframe["close"] < dataframe["bb_mid"])
                | (dataframe["adx"] < 20)
            ),
            "exit_short",
        ] = 1
        dataframe["exit_long"] = 0
        return dataframe
