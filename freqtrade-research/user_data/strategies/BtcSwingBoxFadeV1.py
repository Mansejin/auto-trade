# pragma pylint: disable=missing-docstring, invalid-name
"""BTC swing-box fade — fixed swing S/R, ≥2 touches, rejection only.

Card: docs/research/btc-swing-box-fade-card-frozen.md
Hypers: touch_frac=0.15, wick_body_k=1.5, min_touches=2
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, stoploss_from_absolute
import talib.abstract as ta


class BtcSwingBoxFadeV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 80

    touch_frac = 0.15
    wick_body_k = 1.5
    min_touches = 2

    pivot_left = 3
    width_min = 0.01
    width_max = 0.02
    adx_max = 25.0
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
        o = dataframe["open"].to_numpy(dtype=float)
        h = dataframe["high"].to_numpy(dtype=float)
        l = dataframe["low"].to_numpy(dtype=float)
        c = dataframe["close"].to_numpy(dtype=float)
        n = len(c)
        left = self.pivot_left
        win = 2 * left + 1

        adx = ta.ADX(dataframe, timeperiod=14).to_numpy(dtype=float)

        box_hh = np.full(n, np.nan)
        box_ll = np.full(n, np.nan)
        box_mid = np.full(n, np.nan)
        fade_long = np.zeros(n, dtype=bool)
        fade_short = np.zeros(n, dtype=bool)
        stop_long = np.full(n, np.nan)
        stop_short = np.full(n, np.nan)

        last_ph = np.nan
        last_pl = np.nan
        cur_hh = np.nan
        cur_ll = np.nan
        touches_h = 0
        touches_l = 0
        last_sig = -10**9

        for i in range(n):
            # confirm pivots (pivot bar = i-left)
            if i >= win - 1:
                w0 = i - win + 1
                seg_h = h[w0 : i + 1]
                seg_l = l[w0 : i + 1]
                piv_i = i - left
                if seg_h.argmax() == left:
                    last_ph = h[piv_i]
                if seg_l.argmin() == left:
                    last_pl = l[piv_i]

            # (re)build box from latest swing pair
            if np.isfinite(last_ph) and np.isfinite(last_pl) and last_ph > last_pl:
                mid = 0.5 * (last_ph + last_pl)
                width = (last_ph - last_pl) / mid if mid > 0 else 0.0
                if self.width_min <= width <= self.width_max:
                    if last_ph != cur_hh or last_pl != cur_ll:
                        cur_hh, cur_ll = last_ph, last_pl
                        touches_h = 0
                        touches_l = 0
                else:
                    # pair exists but width wrong — keep old box if still valid
                    pass

            # invalidate on close break — need fresh swings
            if np.isfinite(cur_hh) and (c[i] > cur_hh or c[i] < cur_ll):
                cur_hh = cur_ll = np.nan
                touches_h = touches_l = 0
                last_ph = last_pl = np.nan
                continue

            if not (np.isfinite(cur_hh) and np.isfinite(cur_ll)):
                continue

            span = cur_hh - cur_ll
            mid = 0.5 * (cur_hh + cur_ll)
            edge_lo = cur_ll + self.touch_frac * span
            edge_hi = cur_hh - self.touch_frac * span

            if h[i] >= edge_hi:
                touches_h += 1
            if l[i] <= edge_lo:
                touches_l += 1

            box_hh[i] = cur_hh
            box_ll[i] = cur_ll
            box_mid[i] = mid
            stop_long[i] = l[i]
            stop_short[i] = h[i]

            if adx[i] >= self.adx_max or (i - last_sig) < self.cooldown_bars:
                continue

            body = abs(c[i] - o[i])
            if body < 1e-12:
                body = 1e-12
            lower_wick = min(o[i], c[i]) - l[i]
            upper_wick = h[i] - max(o[i], c[i])

            long_ok = (
                touches_l >= self.min_touches
                and l[i] <= edge_lo
                and c[i] > edge_lo
                and c[i] > o[i]
                and lower_wick >= self.wick_body_k * body
            )
            short_ok = (
                touches_h >= self.min_touches
                and h[i] >= edge_hi
                and c[i] < edge_hi
                and c[i] < o[i]
                and upper_wick >= self.wick_body_k * body
            )
            if long_ok:
                fade_long[i] = True
                last_sig = i
            elif short_ok:
                fade_short[i] = True
                last_sig = i

        dataframe["box_hh"] = box_hh
        dataframe["box_ll"] = box_ll
        dataframe["box_mid"] = box_mid
        dataframe["box_stop_long"] = stop_long
        dataframe["box_stop_short"] = stop_short
        dataframe["fade_long"] = fade_long
        dataframe["fade_short"] = fade_short
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
        mid = prior.iloc[-1]["box_mid"]
        if mid != mid:  # NaN
            return None
        mid = float(mid)
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
        if stop <= 0 or stop != stop:
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
    assert BtcSwingBoxFadeV1.min_touches == 2
    print("BtcSwingBoxFadeV1 self-check OK")
