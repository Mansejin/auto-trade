# pragma pylint: disable=missing-docstring, invalid-name
"""LIVE SCALP — Bitget port of strategies/daytrade-edge-10m-div-atr-v1.json

Bitget has no 10m — same encoding on **15m** (ponytail: TF platform constraint).
Long-only divergence @ BB lower + ATR rising → exit BB upper.
SL 0.8% / ROI 2.5%. Fee 0.06%.
Promoted for bear-regime SCALP sleeve (장타 Policy C stays on Upbit).
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class DaytradeEdge10mDivAtrV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "15m"
    startup_candle_count = 40

    stoploss = -0.008
    minimal_roi = {"0": 0.025}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lower"] = bb["lower"]
        dataframe["bb_mid"] = bb["mid"]
        dataframe["bb_upper"] = bb["upper"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        classic = (
            (dataframe["low"] > dataframe["low"].shift(3))
            & (dataframe["rsi"] < dataframe["rsi"].shift(3))
            & (dataframe["close"] <= dataframe["bb_lower"])
        )
        hidden = (
            (dataframe["low"] < dataframe["low"].shift(3))
            & (dataframe["rsi"] > dataframe["rsi"].shift(3))
            & (dataframe["close"] <= dataframe["bb_lower"])
        )
        dataframe.loc[
            (
                (dataframe["atr"] > dataframe["atr"].shift(3))
                & (classic | hidden)
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] >= dataframe["bb_upper"]),
            "exit_long",
        ] = 1
        dataframe["exit_short"] = 0
        return dataframe
