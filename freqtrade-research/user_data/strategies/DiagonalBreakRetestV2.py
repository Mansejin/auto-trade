# pragma pylint: disable=missing-docstring, invalid-name
"""빗각 단타 v2 — LR channel break & failed-retest (Bitget ETH 5m).

v1 (first-touch reject at rail) falsified on all windows (PF 0.18–0.51).
Hypothesis (v2): Discretionary 빗각 often waits for a *failed break* of the
angled rail, then shorts/longs the reclaim — not the first touch.

Entry short:
  LR slope(40) < 0
  AND close was > LR_upper within prior 3 bars
  AND close crossed_below LR_upper
  AND close < open
Entry long: symmetric on lower rail / positive slope
Exit: ROI +0.60% / SL -0.30% OR back to LR mid

Fee baseline 0.06% taker; optional maker stress in notes.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class DiagonalBreakRetestV2(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 60

    stoploss = -0.003
    minimal_roi = {"0": 0.006}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    lr_period = 40
    lr_stds = 2.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        p = self.lr_period
        dataframe["lr_mid"] = ta.LINEARREG(dataframe, timeperiod=p)
        dataframe["lr_slope"] = ta.LINEARREG_SLOPE(dataframe, timeperiod=p)
        resid = dataframe["close"] - dataframe["lr_mid"]
        dataframe["lr_std"] = resid.rolling(p).std()
        dataframe["lr_upper"] = dataframe["lr_mid"] + self.lr_stds * dataframe["lr_std"]
        dataframe["lr_lower"] = dataframe["lr_mid"] - self.lr_stds * dataframe["lr_std"]
        dataframe["above_upper_3"] = (
            (dataframe["close"] > dataframe["lr_upper"])
            .rolling(3)
            .max()
            .fillna(0)
            .astype(bool)
        )
        dataframe["below_lower_3"] = (
            (dataframe["close"] < dataframe["lr_lower"])
            .rolling(3)
            .max()
            .fillna(0)
            .astype(bool)
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["lr_slope"] < 0)
                & (dataframe["above_upper_3"])
                & (qtpylib.crossed_below(dataframe["close"], dataframe["lr_upper"]))
                & (dataframe["close"] < dataframe["open"])
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        dataframe.loc[
            (
                (dataframe["lr_slope"] > 0)
                & (dataframe["below_lower_3"])
                & (qtpylib.crossed_above(dataframe["close"], dataframe["lr_lower"]))
                & (dataframe["close"] > dataframe["open"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] <= dataframe["lr_mid"]), "exit_short"] = 1
        dataframe.loc[(dataframe["close"] >= dataframe["lr_mid"]), "exit_long"] = 1
        return dataframe
