# pragma pylint: disable=missing-docstring, invalid-name
"""빗각(대각 채널) 단타 v1 — Bitget ETHUSDT-M 5m (research).

Maps discretionary '빗각 매매' (angled trendline / fib-channel style) to a
testable rule: trade mean-reversion *along* a short linear-regression channel.

Hypothesis: When the 5m regression slope is negative, touches of the upper
channel reject back toward the midline more often than they break out (and
symmetric for positive slope → long from lower channel). Short TF, but TP
sized to clear Bitget taker RT (~0.12%).

Entry short:
  LR slope(40) < 0
  AND close >= LR_upper (mid + 2*resid_std)
  AND close < open          (reject candle)
Entry long:
  LR slope(40) > 0
  AND close <= LR_lower
  AND close > open
Exit:
  ROI +0.50% / SL -0.25%
  OR short: close <= LR mid / long: close >= LR mid

Falsify if ≥2/3 windows: PF<1 or return<0.
Not CORE Policy C. SCALP research only.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class DiagonalChannelScalpV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 60

    stoploss = -0.0025
    minimal_roi = {"0": 0.005}
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
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Short: falling diagonal, reject at upper rail
        dataframe.loc[
            (
                (dataframe["lr_slope"] < 0)
                & (dataframe["close"] >= dataframe["lr_upper"])
                & (dataframe["close"] < dataframe["open"])
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        # Long: rising diagonal, bounce at lower rail
        dataframe.loc[
            (
                (dataframe["lr_slope"] > 0)
                & (dataframe["close"] <= dataframe["lr_lower"])
                & (dataframe["close"] > dataframe["open"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] <= dataframe["lr_mid"]),
            "exit_short",
        ] = 1
        dataframe.loc[
            (dataframe["close"] >= dataframe["lr_mid"]),
            "exit_long",
        ] = 1
        return dataframe
