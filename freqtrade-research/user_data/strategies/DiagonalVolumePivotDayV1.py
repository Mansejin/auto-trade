# pragma pylint: disable=missing-docstring, invalid-name
"""빗각 V1 day — volume-pivot parallel channel, BTC 15m (research).

User target: ~3–4 day trades on liquid BTC days; skip thin days.
Anchors: swing high/low where volume >= k * SMA(volume).
Channel: 저저고 (2 lows + 1 high) or 고고저 (2 highs + 1 low).
Mode A only: rising → long lower rail; falling → short upper rail.

Hypothesis: Volume-pivoted rails beat LR(40)±2σ proxies on 15m BTC
when a daily liquidity gate is on.

Falsify if ≥2/3 windows: PF<1 or net return<0.
Not CORE / LIVE.
"""
from __future__ import annotations

import numpy as np
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta


class DiagonalVolumePivotDayV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 220

    # Day-scalp sizing: cover ~0.12% RT fee with room; rail mid is primary exit.
    stoploss = -0.005
    minimal_roi = {"0": 0.01}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    # Frozen hypers (change one at a time after falsify — do not tune live).
    vol_sma = 20
    vol_k = 1.5
    swing = 3
    lookback = 192  # 2d of 15m
    touch_pct = 0.0015  # 0.15% of rail
    liq_k = 0.75  # day vol vs 20d SMA
    liq_sma = 20

    def informative_pairs(self):
        if not self.dp:
            return []
        return [(pair, "1d") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = self.vol_sma
        k = self.vol_k
        swing = self.swing
        L = self.lookback

        vol_ma = dataframe["volume"].rolling(n).mean()
        win = swing * 2 + 1
        # Causal swing: center of window ending at i is bar i-swing
        roll_max = dataframe["high"].rolling(win).max()
        roll_min = dataframe["low"].rolling(win).min()
        is_ph = dataframe["high"].shift(swing) == roll_max
        is_pl = dataframe["low"].shift(swing) == roll_min
        vol_at = dataframe["volume"].shift(swing)
        vol_ma_at = vol_ma.shift(swing)
        vol_ok = vol_at >= (k * vol_ma_at)
        dataframe["vol_ph"] = (is_ph & vol_ok).fillna(False)
        dataframe["vol_pl"] = (is_pl & vol_ok).fillna(False)

        # Mark pivot prices at confirmation bar (lagged swing bars)
        dataframe["ph_price"] = np.where(dataframe["vol_ph"], dataframe["high"].shift(swing), np.nan)
        dataframe["pl_price"] = np.where(dataframe["vol_pl"], dataframe["low"].shift(swing), np.nan)
        dataframe["ph_idx"] = np.where(dataframe["vol_ph"], np.arange(len(dataframe)) - swing, np.nan)
        dataframe["pl_idx"] = np.where(dataframe["vol_pl"], np.arange(len(dataframe)) - swing, np.nan)

        upper, lower, mid, slope, valid = self._build_channel(dataframe, L)
        dataframe["ch_upper"] = upper
        dataframe["ch_lower"] = lower
        dataframe["ch_mid"] = mid
        dataframe["ch_slope"] = slope
        dataframe["ch_valid"] = valid

        # Daily liquidity gate (BTC day volume vs its SMA)
        dataframe["day_liquid"] = True
        if self.dp:
            inf = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="1d")
            if inf is not None and not inf.empty:
                inf = inf.copy()
                inf["day_vol_ma"] = inf["volume"].rolling(self.liq_sma).mean()
                inf["day_liquid"] = inf["volume"] >= (self.liq_k * inf["day_vol_ma"])
                dataframe = merge_informative_pair(
                    dataframe, inf, self.timeframe, "1d", ffill=True
                )
                dataframe["day_liquid"] = (
                    dataframe["day_liquid_1d"].fillna(False).astype(bool)
                )

        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    @staticmethod
    def _build_channel(dataframe: DataFrame, L: int):
        n = len(dataframe)
        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        vol_ph = dataframe["vol_ph"].to_numpy(dtype=bool)
        vol_pl = dataframe["vol_pl"].to_numpy(dtype=bool)
        # Pivot event is confirmed at bar i, but price/index refer to i-swing
        ph_price = dataframe["ph_price"].to_numpy(dtype=float)
        pl_price = dataframe["pl_price"].to_numpy(dtype=float)
        ph_idx = dataframe["ph_idx"].to_numpy(dtype=float)
        pl_idx = dataframe["pl_idx"].to_numpy(dtype=float)

        upper = np.full(n, np.nan)
        lower = np.full(n, np.nan)
        mid = np.full(n, np.nan)
        slope = np.full(n, np.nan)
        valid = np.zeros(n, dtype=bool)

        # Confirmed pivots as (anchor_bar_index, price)
        phs: list[tuple[int, float]] = []
        pls: list[tuple[int, float]] = []

        for i in range(n):
            if vol_ph[i] and not np.isnan(ph_price[i]) and not np.isnan(ph_idx[i]):
                phs.append((int(ph_idx[i]), float(ph_price[i])))
            if vol_pl[i] and not np.isnan(pl_price[i]) and not np.isnan(pl_idx[i]):
                pls.append((int(pl_idx[i]), float(pl_price[i])))

            while phs and phs[0][0] < i - L:
                phs.pop(0)
            while pls and pls[0][0] < i - L:
                pls.pop(0)

            cand: list[tuple[float, float, float, float]] = []  # slope, upper, lower, score

            # 저저고 — rising / support channel
            if len(pls) >= 2 and len(phs) >= 1:
                (i1, p1), (i2, p2) = pls[-2], pls[-1]
                i3, p3 = phs[-1]
                if i2 > i1:
                    s = (p2 - p1) / (i2 - i1)
                    lo = p2 + s * (i - i2)
                    up = p3 + s * (i - i3)
                    if up > lo and s >= 0:
                        cand.append((s, up, lo, i2 + i3))

            # 고고저 — falling / resistance channel
            if len(phs) >= 2 and len(pls) >= 1:
                (i1, p1), (i2, p2) = phs[-2], phs[-1]
                i3, p3 = pls[-1]
                if i2 > i1:
                    s = (p2 - p1) / (i2 - i1)
                    up = p2 + s * (i - i2)
                    lo = p3 + s * (i - i3)
                    if up > lo and s <= 0:
                        cand.append((s, up, lo, i2 + i3))

            if not cand:
                continue
            # Most recent anchors win
            s, up, lo, _ = max(cand, key=lambda t: t[3])
            slope[i] = s
            upper[i] = up
            lower[i] = lo
            mid[i] = 0.5 * (up + lo)
            valid[i] = True

        return upper, lower, mid, slope, valid

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        tol = self.touch_pct
        near_lower = (
            (dataframe["low"] <= dataframe["ch_lower"] * (1 + tol))
            & (dataframe["close"] >= dataframe["ch_lower"] * (1 - tol))
        )
        near_upper = (
            (dataframe["high"] >= dataframe["ch_upper"] * (1 - tol))
            & (dataframe["close"] <= dataframe["ch_upper"] * (1 + tol))
        )
        base = (
            dataframe["ch_valid"]
            & dataframe["day_liquid"]
            & (dataframe["volume"] > 0)
        )

        # Long: rising channel, bounce at lower rail (close back above rail)
        dataframe.loc[
            (
                base
                & (dataframe["ch_slope"] > 0)
                & near_lower
                & (dataframe["close"] > dataframe["open"])
                & (dataframe["close"] > dataframe["ch_lower"])
            ),
            "enter_long",
        ] = 1

        # Short: falling channel, reject at upper rail
        dataframe.loc[
            (
                base
                & (dataframe["ch_slope"] < 0)
                & near_upper
                & (dataframe["close"] < dataframe["open"])
                & (dataframe["close"] < dataframe["ch_upper"])
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Mode A: take mid (or opposite rail via ROI/SL)
        dataframe.loc[
            dataframe["ch_valid"] & (dataframe["close"] >= dataframe["ch_mid"]),
            "exit_long",
        ] = 1
        dataframe.loc[
            dataframe["ch_valid"] & (dataframe["close"] <= dataframe["ch_mid"]),
            "exit_short",
        ] = 1
        return dataframe


if __name__ == "__main__":
    # ponytail: one assert that channel geometry stays sane on a toy series
    import pandas as pd

    idx = pd.date_range("2026-01-01", periods=40, freq="15min")
    close = np.linspace(100, 110, 40)
    high = close + 1
    low = close - 1
    low[10] = 99.0
    low[20] = 101.0
    high[25] = 112.0
    vol = np.full(40, 100.0)
    vol[[10, 20, 25]] = 500.0
    df = pd.DataFrame(
        {
            "date": idx,
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": vol,
        }
    )
    n = 20
    swing = 3
    vol_ma = df["volume"].rolling(n).mean()
    win = swing * 2 + 1
    roll_max = df["high"].rolling(win).max()
    roll_min = df["low"].rolling(win).min()
    is_ph = df["high"].shift(swing) == roll_max
    is_pl = df["low"].shift(swing) == roll_min
    vol_ok = df["volume"].shift(swing) >= (1.5 * vol_ma.shift(swing))
    df["vol_ph"] = (is_ph & vol_ok).fillna(False)
    df["vol_pl"] = (is_pl & vol_ok).fillna(False)
    df["ph_price"] = np.where(df["vol_ph"], df["high"].shift(swing), np.nan)
    df["pl_price"] = np.where(df["vol_pl"], df["low"].shift(swing), np.nan)
    df["ph_idx"] = np.where(df["vol_ph"], np.arange(len(df)) - swing, np.nan)
    df["pl_idx"] = np.where(df["vol_pl"], np.arange(len(df)) - swing, np.nan)
    upper, lower, mid, slope, valid = DiagonalVolumePivotDayV1._build_channel(df, 192)
    assert df["vol_pl"].any() or df["vol_ph"].any(), "expected volume pivots"
    if valid.any():
        j = int(np.where(valid)[0][-1])
        assert upper[j] > lower[j], "upper must be above lower"
    print("DiagonalVolumePivotDayV1 self-check OK")
