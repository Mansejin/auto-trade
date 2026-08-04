# pragma pylint: disable=missing-docstring, invalid-name
"""Bear short breakdown + volume v6 — Bitget BTCUSDT-M (research / scalp sleeve).

Prior fade/momentum shorts (v1–v5) falsified or sample-starved.
Hypothesis (v6): On 1h bear (EMA50<EMA200), a 15m close that breaks BB lower
with volume ≥ 1.5× SMA20 and ADX≥25 is a continuation dump — short the break.

Entry (short only):
  EMA50_1h < EMA200_1h
  AND close crossed_below BB lower(20,2)
  AND volume >= 1.5 * SMA(volume, 20)
  AND ADX(14) >= 25
Exit:
  ROI +1.5% / SL -0.7%
  OR close > BB mid OR ADX < 18

Fee 0.06% taker. No threshold retune after scoring.
Not a Policy C replacement — intended as SCALP sleeve capital only.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta
from technical import qtpylib


class BearShortBreakdownVolV6(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 220

    stoploss = -0.007
    minimal_roi = {"0": 0.015}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, "1h") for pair in pairs]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["vol_sma20"] = ta.SMA(dataframe["volume"], timeperiod=20)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lower"] = bb["lower"]
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
                & (qtpylib.crossed_below(dataframe["close"], dataframe["bb_lower"]))
                & (dataframe["volume"] >= 1.5 * dataframe["vol_sma20"])
                & (dataframe["adx"] >= 25)
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] > dataframe["bb_mid"])
                | (dataframe["adx"] < 18)
            ),
            "exit_short",
        ] = 1
        dataframe["exit_long"] = 0
        return dataframe
