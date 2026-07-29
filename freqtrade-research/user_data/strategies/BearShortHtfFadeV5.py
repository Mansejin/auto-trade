# pragma pylint: disable=missing-docstring, invalid-name
"""Bear-regime short scalp v5 — Bitget BTCUSDT-M (research).

v4 used RSI>65 level (continuous) → 127–203 trades/window, PF 0.38–0.81.
That was a trigger bug relative to the fade hypothesis, not a retune.

Hypothesis (v5): On 1h bear (EMA50<EMA200), short the *start* of a 5m pop
(RSI crosses above 65 while above BB mid), not every bar while elevated.

Entry (short only):
  EMA50_1h < EMA200_1h
  AND RSI crossed_above 65
  AND close > BB mid
  AND ADX >= 18
Exit:
  ROI +1.0% / SL -0.45%
  OR RSI < 45 OR close < BB mid OR ADX < 15

Fee 0.06%. No Policy C change without approve.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta
from technical import qtpylib


class BearShortHtfFadeV5(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 220

    stoploss = -0.0045
    minimal_roi = {"0": 0.01}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, "1h") for pair in pairs]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_mid"] = bb["mid"]

        informative = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="1h")
        informative["ema50"] = ta.EMA(informative, timeperiod=50)
        informative["ema200"] = ta.EMA(informative, timeperiod=200)
        dataframe = merge_informative_pair(
            dataframe, informative, self.timeframe, "1h", ffill=True
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema50_1h"] < dataframe["ema200_1h"])
                & (qtpylib.crossed_above(dataframe["rsi"], 65))
                & (dataframe["close"] > dataframe["bb_mid"])
                & (dataframe["adx"] >= 18)
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
                | (dataframe["adx"] < 15)
            ),
            "exit_short",
        ] = 1
        dataframe["exit_long"] = 0
        return dataframe
