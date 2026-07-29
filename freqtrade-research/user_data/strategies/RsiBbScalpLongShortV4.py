# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
"""RSI+BB mean-reversion scalp — Bitget BTCUSDT-M long/short (research).

Mirrors auto-trade strategies/krw-btc-5m-scalp-rsi-bb-long-v4 + short side:
  Long:  RSI < 25 AND close < BB lower AND ADX < 30
  Short: RSI > 75 AND close > BB upper AND ADX < 30
  Exit:  ROI +0.8% / stoploss -0.3% (TP/SL only; no indicator exit)

Do not mount to LIVE / Policy C from this alone.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class RsiBbScalpLongShortV4(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 40

    # Bitget-fee-aware RR from research notes
    stoploss = -0.003
    minimal_roi = {"0": 0.008}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=20, stds=2
        )
        dataframe["bb_lower"] = bollinger["lower"]
        dataframe["bb_middle"] = bollinger["mid"]
        dataframe["bb_upper"] = bollinger["upper"]
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] < 25)
                & (dataframe["close"] < dataframe["bb_lower"])
                & (dataframe["adx"] < 30)
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1

        dataframe.loc[
            (
                (dataframe["rsi"] > 75)
                & (dataframe["close"] > dataframe["bb_upper"])
                & (dataframe["adx"] < 30)
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # TP/SL only — ROI + stoploss handle exits
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
