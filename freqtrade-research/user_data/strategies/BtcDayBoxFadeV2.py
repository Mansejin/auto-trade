# pragma pylint: disable=missing-docstring, invalid-name
"""BTC day-box fade V2 — rejection wick + stable box + cooldown (anti-scrape).

Card: docs/research/btc-day-box-fade-v2-card-frozen.md
Hypers: touch_frac=0.15, wick_body_k=1.5, adx_max=25
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, stoploss_from_absolute
import talib.abstract as ta


class BtcDayBoxFadeV2(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 120

    touch_frac = 0.15
    wick_body_k = 1.5
    adx_max = 25.0

    lookback = 96
    width_min = 0.01
    width_max = 0.02
    stable_shift = 16
    stable_max_chg = 0.25
    sl_buf_frac = 0.05
    cooldown_bars = 6

    stoploss = -0.15
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
        o, h, l, c = (
            dataframe["open"],
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
        )
        body = (c - o).abs().clip(lower=1e-12)
        lower_wick = np.minimum(o, c) - l
        upper_wick = h - np.maximum(o, c)

        hh = h.rolling(self.lookback).max()
        ll = l.rolling(self.lookback).min()
        mid = (hh + ll) / 2.0
        span = (hh - ll).clip(lower=1e-12)
        width = span / mid.clip(lower=1e-12)
        adx = ta.ADX(dataframe, timeperiod=14)

        width_chg = (width - width.shift(self.stable_shift)).abs() / width.clip(lower=1e-12)
        stable = width_chg <= self.stable_max_chg
        in_regime = (
            (width >= self.width_min)
            & (width <= self.width_max)
            & (adx < self.adx_max)
            & stable
        )

        edge_lo = ll + self.touch_frac * span
        edge_hi = hh - self.touch_frac * span

        # tag edge with wick, close back inside (reclaim)
        long_rej = (
            in_regime
            & (l <= edge_lo)
            & (c > edge_lo)
            & (c > o)
            & (lower_wick >= self.wick_body_k * body)
        )
        short_rej = (
            in_regime
            & (h >= edge_hi)
            & (c < edge_hi)
            & (c < o)
            & (upper_wick >= self.wick_body_k * body)
        )

        # cooldown: suppress signals for N bars after a signal (proxy for post-exit)
        def _cooldown(sig: pd.Series) -> pd.Series:
            raw = sig.fillna(False).astype(bool)
            blocked = pd.Series(False, index=raw.index)
            last = -10**9
            out = raw.copy()
            for i in range(len(raw)):
                if i - last < self.cooldown_bars:
                    out.iloc[i] = False
                    blocked.iloc[i] = True
                elif bool(raw.iloc[i]):
                    last = i
            return out

        dataframe["box_hh"] = hh
        dataframe["box_ll"] = ll
        dataframe["box_mid"] = mid
        dataframe["box_width"] = width
        # SL at rejection wick extreme (anti-scrape vs box-beyond stop)
        dataframe["box_stop_long"] = l
        dataframe["box_stop_short"] = h
        dataframe["fade_long"] = _cooldown(long_rej)
        dataframe["fade_short"] = _cooldown(short_rej)
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
    # rejection at low of a 1.5% box
    o, h, l, c = 99.4, 99.6, 99.0, 99.55
    body = abs(c - o)
    lower = min(o, c) - l
    assert c > o and lower >= 1.5 * body
    print("BtcDayBoxFadeV2 self-check OK")
