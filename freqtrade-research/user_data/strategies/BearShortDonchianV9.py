# pragma pylint: disable=missing-docstring, invalid-name
"""Bear short SCALP sleeve v9 — Donchian breakdown, ROI/SL only (Bitget).

v7 reclaim and v8 1h DI both falsified; exit-signal fades often cut losers
before ROI. Hypothesis (v9): In 1h bear, short a fresh 20-bar low break on 15m
with volume confirmation; hold only for ROI +2.5% / SL -1.0% (no signal exit).

Entry (short only):
  EMA50_1h < EMA200_1h
  AND close crossed_below rolling_min(low, 20).shift(1)
  AND volume >= 1.2 * SMA(volume, 20)
  AND ADX >= 22
Exit:
  ROI +2.5% / SL -1.0% only (use_exit_signal=False)

Fee 0.06%. SCALP sleeve only.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta
from technical import qtpylib


class BearShortDonchianV9(IStrategy):
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
        return [(pair, "1h") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["vol_sma20"] = ta.SMA(dataframe["volume"], timeperiod=20)
        # Prior 20-bar low (exclude current bar) for true breakout trigger
        dataframe["donchian_low"] = dataframe["low"].rolling(20).min().shift(1)

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
                & (qtpylib.crossed_below(dataframe["close"], dataframe["donchian_low"]))
                & (dataframe["volume"] >= 1.2 * dataframe["vol_sma20"])
                & (dataframe["adx"] >= 22)
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
