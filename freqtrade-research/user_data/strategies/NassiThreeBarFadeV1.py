# pragma pylint: disable=missing-docstring, invalid-name
"""나씨 3-bar fade CORE — 5m long same-color run → fade opposite.

Card: docs/research/nassi-3bar-fade-card-frozen.md
Hypers (frozen): body_k=1.5, min_body_pct=0.0015, body_lookback=20

Universe: BTC 5m 24h. Long+Short. No averaging / no no-stop.
Falsify if ≥2/3 ~30d windows: PF<1 or net<0.
Not CORE / LIVE until survive.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, stoploss_from_absolute


class NassiThreeBarFadeV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 40

    # --- frozen hypers (≤3) ---
    body_k = 1.5
    min_body_pct = 0.0015
    body_lookback = 20

    stoploss = -0.05  # hard floor; real stop = 3-bar impulse extreme
    use_custom_stoploss = True
    minimal_roi = {"0": 0.005}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        o = dataframe["open"]
        h = dataframe["high"]
        l = dataframe["low"]
        c = dataframe["close"]
        body = (c - o).abs()
        med = body.rolling(self.body_lookback).median()
        long_bar = (body >= self.body_k * med) & (body / c.clip(lower=1e-12) >= self.min_body_pct)
        green = c > o
        red = c < o

        bull3 = (
            long_bar
            & long_bar.shift(1)
            & long_bar.shift(2)
            & green
            & green.shift(1)
            & green.shift(2)
        )
        bear3 = (
            long_bar
            & long_bar.shift(1)
            & long_bar.shift(2)
            & red
            & red.shift(1)
            & red.shift(2)
        )

        dataframe["fade_short"] = bull3.fillna(False)
        dataframe["fade_long"] = bear3.fillna(False)
        # Stop for long fade = low of 3-bar bear run; short fade = high of bull run
        dataframe["fade_stop_long"] = np.minimum(np.minimum(l, l.shift(1)), l.shift(2))
        dataframe["fade_stop_short"] = np.maximum(np.maximum(h, h.shift(1)), h.shift(2))
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
        col = "fade_stop_short" if trade.is_short else "fade_stop_long"
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
    # 3 long green bars after quiet median → fade_short; mixed colors → no signal
    body_k, min_body_pct, lookback = 1.5, 0.0015, 20
    o = np.array([100.0] * 25)
    c = np.array([100.0] * 25)
    h = np.array([100.2] * 25)
    l = np.array([99.8] * 25)
    for i in range(20):
        o[i], c[i] = 100.0, 100.05
        h[i], l[i] = 100.1, 99.95
    for i, (oo, cc) in enumerate([(100.0, 100.4), (100.4, 100.8), (100.8, 101.2)], start=20):
        o[i], c[i] = oo, cc
        h[i], l[i] = cc + 0.05, oo - 0.05
    body = np.abs(c - o)
    med = pd.Series(body).rolling(lookback).median().to_numpy()
    long_bar = (body >= body_k * med) & (body / np.maximum(c, 1e-12) >= min_body_pct)
    green = c > o
    bull3 = long_bar & np.roll(long_bar, 1) & np.roll(long_bar, 2) & green & np.roll(green, 1) & np.roll(green, 2)
    bull3[:2] = False
    assert bool(bull3[22])
    green2 = green.copy()
    green2[22] = False  # break color
    bull3b = long_bar & np.roll(long_bar, 1) & np.roll(long_bar, 2) & green2 & np.roll(green2, 1) & np.roll(green2, 2)
    bull3b[:2] = False
    assert not bool(bull3b[22])
    print("NassiThreeBarFadeV1 self-check OK")
