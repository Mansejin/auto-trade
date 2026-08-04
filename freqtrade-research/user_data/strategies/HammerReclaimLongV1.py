# pragma pylint: disable=missing-docstring, invalid-name
"""Hammer reclaim long — long lower-wick + green → long; SL at wick low.

Card: docs/research/hammer-reclaim-long-card-frozen.md
Hypers (frozen): wick_body_k=2.0, min_wick_frac=0.55, body_max_frac=0.35

Universe: BTC/ETH/SOL 15m 24h. Long only.
Falsify if ≥2/3 ~30d windows: PF<1 or net<0.
Not CORE / LIVE.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, stoploss_from_absolute


class HammerReclaimLongV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "15m"
    startup_candle_count = 20

    # --- frozen hypers (≤3) ---
    wick_body_k = 2.0
    min_wick_frac = 0.55
    body_max_frac = 0.35

    stoploss = -0.05  # hard floor; real stop = signal low
    use_custom_stoploss = True
    minimal_roi = {"0": 0.01}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        o = dataframe["open"]
        h = dataframe["high"]
        l = dataframe["low"]
        c = dataframe["close"]
        body = (c - o).abs()
        rng = (h - l).clip(lower=1e-12)
        lower = np.minimum(o, c) - l
        upper = h - np.maximum(o, c)

        dataframe["hammer"] = (
            (c > o)
            & (lower >= self.wick_body_k * body)
            & (lower >= self.min_wick_frac * rng)
            & (body <= self.body_max_frac * rng)
            & (lower > upper)
        )
        dataframe["hammer_stop"] = l
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["hammer"] & (dataframe["volume"] > 0),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
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
        # Signal on closed bar N → fill on N+1; stop = bar N low.
        ts = pd.to_datetime(dataframe["date"], utc=True)
        opened = pd.Timestamp(trade.open_date_utc)
        if opened.tzinfo is None:
            opened = opened.tz_localize("UTC")
        else:
            opened = opened.tz_convert("UTC")
        prior = dataframe.loc[ts < opened]
        if prior.empty:
            return None
        stop = float(prior.iloc[-1]["hammer_stop"])
        if stop <= 0:
            return None
        if stop >= current_rate:
            stop = current_rate * 0.999
        return stoploss_from_absolute(
            stop_rate=stop,
            current_rate=current_rate,
            is_short=False,
            leverage=trade.leverage or 1.0,
        )


if __name__ == "__main__":
    import pandas as pd

    df = pd.DataFrame(
        {
            "open": [100.0, 100.0],
            "high": [101.0, 100.5],
            "low": [97.0, 99.8],
            "close": [100.5, 100.2],
            "volume": [1.0, 1.0],
        }
    )
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    body = (c - o).abs()
    rng = (h - l).clip(lower=1e-12)
    lower = np.minimum(o, c) - l
    upper = h - np.maximum(o, c)
    hammer = (
        (c > o)
        & (lower >= 2.0 * body)
        & (lower >= 0.55 * rng)
        & (body <= 0.35 * rng)
        & (lower > upper)
    )
    assert bool(hammer.iloc[0]) and not bool(hammer.iloc[1])
    print("HammerReclaimLongV1 self-check OK")
