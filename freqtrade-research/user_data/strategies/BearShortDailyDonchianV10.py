# pragma pylint: disable=missing-docstring, invalid-name
"""Bear short SCALP sleeve v10 — 4h-strong bear + 15m Donchian (Bitget).

Daily candles from Bitget API are too short for our windows; use 4h as the
higher-structure gate instead.

Hypothesis: only short when 4h is strongly bearish (ADX>=25, -DI>+DI,
EMA50<EMA200), then take 15m Donchian-20 breakdown with volume; ROI/SL only.

Entry (short only):
  4h: ADX>=25 AND -DI > +DI AND EMA50 < EMA200
  AND 15m close crossed_below prior 20-bar low
  AND volume >= 1.2 * SMA20
Exit:
  ROI +2.5% / SL -1.0% only

Fee 0.06%. SCALP sleeve only.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta
from technical import qtpylib


class BearShortDailyDonchianV10(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 220

    stoploss = -0.01
    minimal_roi = {"0": 0.025}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    def informative_pairs(self):
        return [(pair, "4h") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["vol_sma20"] = ta.SMA(dataframe["volume"], timeperiod=20)
        dataframe["donchian_low"] = dataframe["low"].rolling(20).min().shift(1)

        htf = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="4h")
        htf["ema50"] = ta.EMA(htf, timeperiod=50)
        htf["ema200"] = ta.EMA(htf, timeperiod=200)
        htf["adx"] = ta.ADX(htf, timeperiod=14)
        htf["plus_di"] = ta.PLUS_DI(htf, timeperiod=14)
        htf["minus_di"] = ta.MINUS_DI(htf, timeperiod=14)
        dataframe = merge_informative_pair(
            dataframe, htf, self.timeframe, "4h", ffill=True
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["adx_4h"] >= 25)
                & (dataframe["minus_di_4h"] > dataframe["plus_di_4h"])
                & (dataframe["ema50_4h"] < dataframe["ema200_4h"])
                & (qtpylib.crossed_below(dataframe["close"], dataframe["donchian_low"]))
                & (dataframe["volume"] >= 1.2 * dataframe["vol_sma20"])
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
