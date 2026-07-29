# pragma pylint: disable=missing-docstring, invalid-name
"""Bear-regime short scalp v4 — Bitget BTCUSDT-M (research).

v1–v3 summary:
  v1 5m RSI>70+BB upper: 0 trades
  v2 5m RSI×50 below EMA: active but PF 0.24–0.78 (falsified)
  v3 15m rally fade: sparse (4/1/1 trades) — direction ok on W1 but n insufficient

Hypothesis (v4): Daily-bear calendar windows still need HTF confirmation.
On 1h bear structure (EMA50 < EMA200), 5m pops into RSI>65 / above BB mid
are short fades. Separate HTF filter from LTF trigger so samples exist.

Entry (short only):
  EMA50_1h < EMA200_1h
  AND RSI(14)_5m > 65
  AND close > BB mid(20,2)
  AND ADX(14)_5m >= 18
Exit:
  ROI +1.0% / SL -0.45%
  OR RSI < 45 OR close < BB mid OR ADX < 15

Fee 0.06%. No retune. No Policy C change without approve.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta
from technical import qtpylib


class BearShortHtfFadeV4(IStrategy):
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
        dataframe["bb_upper"] = bb["upper"]

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
                & (dataframe["rsi"] > 65)
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
