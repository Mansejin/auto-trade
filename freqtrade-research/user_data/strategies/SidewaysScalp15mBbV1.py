# pragma pylint: disable=missing-docstring, invalid-name
"""Sideways SCALP sleeve draft — Bitget BTCUSDT-M 15m BB fade (long+short).

CORE sideways remains Williams 1h / 4h-v5 on Upbit (Policy C). This file is the
separate SCALP-slot candidate only — do not mount on upbit-paper-bot.

Hypothesis: When 15m ADX < 20, fades of BB extremes mean-revert enough to cover
0.06%×2 fees with ROI 1.0% / SL 0.5%.

Entry long:  ADX < 20 AND close crossed_below BB lower
Entry short: ADX < 20 AND close crossed_above BB upper
Exit long:   ROI/SL OR close >= BB mid OR ADX >= 25
Exit short:  ROI/SL OR close <= BB mid OR ADX >= 25

Frozen until multi-window BT. Status in config/sleeves.json: research_draft.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class SidewaysScalp15mBbV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 40

    stoploss = -0.005
    minimal_roi = {"0": 0.01}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lower"] = bb["lower"]
        dataframe["bb_mid"] = bb["mid"]
        dataframe["bb_upper"] = bb["upper"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["adx"] < 20)
                & (qtpylib.crossed_below(dataframe["close"], dataframe["bb_lower"]))
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        dataframe.loc[
            (
                (dataframe["adx"] < 20)
                & (qtpylib.crossed_above(dataframe["close"], dataframe["bb_upper"]))
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
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
        dataframe.loc[
            (
                (dataframe["close"] <= dataframe["bb_mid"])
                | (dataframe["adx"] >= 25)
            ),
            "exit_short",
        ] = 1
        return dataframe
