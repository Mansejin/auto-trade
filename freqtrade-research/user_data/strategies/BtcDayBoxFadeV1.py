# pragma pylint: disable=missing-docstring, invalid-name
"""BTC ~1d box fade — fade 1-2% day range edges; pause on ADX/width.

Card: docs/research/btc-day-box-fade-card-frozen.md
Hypers: touch_frac=0.15, adx_max=25, sl_buf_frac=0.05
Leverage 5. Exit at box mid. SL beyond box.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, stoploss_from_absolute
import talib.abstract as ta


class BtcDayBoxFadeV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 120

    # --- frozen hypers (≤3) ---
    touch_frac = 0.15
    adx_max = 25.0
    sl_buf_frac = 0.05

    # constants
    lookback = 96  # ~1d on 15m
    width_min = 0.01
    width_max = 0.02

    stoploss = -0.15  # lev PnL floor
    use_custom_stoploss = True
    minimal_roi = {"0": 100}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def leverage(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        return min(5.0, max_leverage)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        h, l, c = dataframe["high"], dataframe["low"], dataframe["close"]
        hh = h.rolling(self.lookback).max()
        ll = l.rolling(self.lookback).min()
        mid = (hh + ll) / 2.0
        width = (hh - ll) / mid.clip(lower=1e-12)
        adx = ta.ADX(dataframe, timeperiod=14)
        span = (hh - ll).clip(lower=1e-12)

        in_regime = (
            (width >= self.width_min)
            & (width <= self.width_max)
            & (adx < self.adx_max)
        )
        dataframe["box_hh"] = hh
        dataframe["box_ll"] = ll
        dataframe["box_mid"] = mid
        dataframe["box_width"] = width
        dataframe["box_adx"] = adx
        dataframe["box_regime"] = in_regime.fillna(False)
        dataframe["box_stop_long"] = ll - self.sl_buf_frac * span
        dataframe["box_stop_short"] = hh + self.sl_buf_frac * span
        dataframe["fade_long"] = (
            in_regime & (c <= ll + self.touch_frac * span)
        ).fillna(False)
        dataframe["fade_short"] = (
            in_regime & (c >= hh - self.touch_frac * span)
        ).fillna(False)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["fade_long"] & (dataframe["volume"] > 0),
            "enter_long",
        ] = 1
        dataframe.loc[
            dataframe["fade_short"] & (dataframe["volume"] > 0),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> str | bool | None:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None
        ts = pd.to_datetime(dataframe["date"], utc=True)
        now = pd.Timestamp(current_time)
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        else:
            now = now.tz_convert("UTC")
        prior = dataframe.loc[ts <= now]
        if prior.empty:
            return None
        mid = float(prior.iloc[-1]["box_mid"])
        if trade.is_short:
            if current_rate <= mid:
                return "box_mid"
        else:
            if current_rate >= mid:
                return "box_mid"
        return None

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        after_fill: bool,
        **kwargs,
    ) -> float | None:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None
        ts = pd.to_datetime(dataframe["date"], utc=True)
        opened = pd.Timestamp(trade.open_date_utc)
        if opened.tzinfo is None:
            opened = opened.tz_localize("UTC")
        else:
            opened = opened.tz_convert("UTC")
        prior = dataframe.loc[ts < opened]
        if prior.empty:
            return None
        col = "box_stop_short" if trade.is_short else "box_stop_long"
        stop = float(prior.iloc[-1][col])
        if stop <= 0:
            return None
        if trade.is_short:
            if stop <= current_rate:
                stop = current_rate * 1.001
        else:
            if stop >= current_rate:
                stop = current_rate * 0.999
        return stoploss_from_absolute(
            stop_rate=stop,
            current_rate=current_rate,
            is_short=bool(trade.is_short),
            leverage=trade.leverage or 1.0,
        )


if __name__ == "__main__":
    # toy: flat mid then range 1.5% → edge touch flags
    n = 120
    close = np.full(n, 100.0)
    high = close + 0.2
    low = close - 0.2
    # last 96 bars: range 99..101 → width 2%
    high[-96:] = 101.0
    low[-96:] = 99.0
    close[-1] = 99.1  # near low
    open_ = close.copy()
    df = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.ones(n),
        }
    )
    hh = df["high"].rolling(96).max()
    ll = df["low"].rolling(96).min()
    mid = (hh + ll) / 2
    width = (hh - ll) / mid
    span = hh - ll
    assert 0.01 <= float(width.iloc[-1]) <= 0.02
    assert float(df["close"].iloc[-1]) <= float(ll.iloc[-1] + 0.15 * span.iloc[-1])
    print("BtcDayBoxFadeV1 self-check OK")
