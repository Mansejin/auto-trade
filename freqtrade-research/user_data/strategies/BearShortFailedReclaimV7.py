# pragma pylint: disable=missing-docstring, invalid-name
"""Bear short SCALP sleeve v7 — failed EMA reclaim (Bitget BTCUSDT-M).

Prior v1–v6: fade/momentum/breakdown all falsified or sample-starved.
Hypothesis (v7): In 1h bear (EMA50<EMA200), a 15m bounce that tags EMA20
then closes back below it (failed reclaim) resumes the downtrend.

Entry (short only):
  EMA50_1h < EMA200_1h
  AND high >= EMA20 (touched reclaim zone this bar or prior close was above)
  AND close crossed_below EMA20
  AND -DI > +DI
  AND ADX >= 20
Exit:
  ROI +2.0% / SL -1.0%
  OR close > EMA20 OR ADX < 15

Fee 0.06%. SCALP sleeve only — does not replace CORE m5-v6.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta
from technical import qtpylib


class BearShortFailedReclaimV7(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 220

    stoploss = -0.01
    minimal_roi = {"0": 0.02}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def informative_pairs(self):
        return [(pair, "1h") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)

        informative = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="1h")
        informative["ema50"] = ta.EMA(informative, timeperiod=50)
        informative["ema200"] = ta.EMA(informative, timeperiod=200)
        dataframe = merge_informative_pair(
            dataframe, informative, self.timeframe, "1h", ffill=True
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        touched = (dataframe["high"] >= dataframe["ema20"]) | (
            dataframe["close"].shift(1) >= dataframe["ema20"].shift(1)
        )
        dataframe.loc[
            (
                (dataframe["ema50_1h"] < dataframe["ema200_1h"])
                & touched
                & (qtpylib.crossed_below(dataframe["close"], dataframe["ema20"]))
                & (dataframe["minus_di"] > dataframe["plus_di"])
                & (dataframe["adx"] >= 20)
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] > dataframe["ema20"])
                | (dataframe["adx"] < 15)
            ),
            "exit_short",
        ] = 1
        dataframe["exit_long"] = 0
        return dataframe
