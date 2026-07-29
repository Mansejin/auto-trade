# pragma pylint: disable=missing-docstring, invalid-name
"""빗각 Multi-TF day — 4h volume-pivot channel, 15m entries (BTC).

Discretionary style the user actually uses: draw 빗각 on higher TF,
take touches on lower TF.

Hypothesis: Same Mode A rules as V1, but rails from 4h volume pivots
(extrapolated onto 15m) beat same-TF 15m drawing (V1 falsified).

Entry 15m:
  rising 4h channel → soft touch lower + green
  falling 4h channel → soft touch upper + red
Exit: 4h mid (extrapolated) / ROI +1% / SL -0.5%
Liquidity: daily vol gate (same as V1)

Falsify if ≥2/3 windows: PF<1 or net<0.
Not CORE / LIVE.
"""
from __future__ import annotations

import numpy as np
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta

from DiagonalVolumePivotDayV1 import DiagonalVolumePivotDayV1


class DiagonalMultiTfDayV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 120

    stoploss = -0.005
    minimal_roi = {"0": 0.01}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    # 4h channel hypers (frozen; mirror V1 idea, longer lookback in 4h bars)
    vol_sma = 20
    vol_k = 1.5
    swing = 3
    lookback_4h = 60  # ~10 days of 4h
    touch_pct = 0.0025  # 0.25% — slightly softer vs V1; 4h rails are wider
    liq_k = 0.75
    liq_sma = 20

    def informative_pairs(self):
        if not self.dp:
            return []
        pairs = self.dp.current_whitelist()
        return [(p, "4h") for p in pairs] + [(p, "1d") for p in pairs]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata["pair"]

        # --- 4h structure ---
        inf4 = self.dp.get_pair_dataframe(pair=pair, timeframe="4h").copy()
        inf4 = self._attach_volume_pivots(inf4)
        up, lo, mid, slope, valid = DiagonalVolumePivotDayV1._build_channel(
            inf4, self.lookback_4h
        )
        inf4["ch_upper"] = up
        inf4["ch_lower"] = lo
        inf4["ch_mid"] = mid
        inf4["ch_slope"] = slope
        inf4["ch_valid"] = valid

        dataframe = merge_informative_pair(
            dataframe, inf4, self.timeframe, "4h", ffill=True
        )

        # Extrapolate diagonal between 4h closes (ffill alone freezes the rail)
        elapsed_h = (
            dataframe["date"] - dataframe["date_4h"]
        ).dt.total_seconds() / 3600.0
        frac_4h = (elapsed_h / 4.0).clip(lower=0).fillna(0)
        sl = dataframe["ch_slope_4h"].fillna(0)
        dataframe["ch_upper"] = dataframe["ch_upper_4h"] + sl * frac_4h
        dataframe["ch_lower"] = dataframe["ch_lower_4h"] + sl * frac_4h
        dataframe["ch_mid"] = dataframe["ch_mid_4h"] + sl * frac_4h
        dataframe["ch_slope"] = dataframe["ch_slope_4h"]
        dataframe["ch_valid"] = dataframe["ch_valid_4h"].fillna(False).astype(bool)

        # --- daily liquidity ---
        dataframe["day_liquid"] = True
        inf1 = self.dp.get_pair_dataframe(pair=pair, timeframe="1d")
        if inf1 is not None and not inf1.empty:
            inf1 = inf1.copy()
            inf1["day_vol_ma"] = inf1["volume"].rolling(self.liq_sma).mean()
            inf1["day_liquid"] = inf1["volume"] >= (self.liq_k * inf1["day_vol_ma"])
            dataframe = merge_informative_pair(
                dataframe, inf1, self.timeframe, "1d", ffill=True
            )
            dataframe["day_liquid"] = (
                dataframe["day_liquid_1d"].fillna(False).astype(bool)
            )

        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def _attach_volume_pivots(self, df: DataFrame) -> DataFrame:
        n, k, swing = self.vol_sma, self.vol_k, self.swing
        vol_ma = df["volume"].rolling(n).mean()
        win = swing * 2 + 1
        roll_max = df["high"].rolling(win).max()
        roll_min = df["low"].rolling(win).min()
        is_ph = df["high"].shift(swing) == roll_max
        is_pl = df["low"].shift(swing) == roll_min
        vol_ok = df["volume"].shift(swing) >= (k * vol_ma.shift(swing))
        df["vol_ph"] = (is_ph & vol_ok).fillna(False)
        df["vol_pl"] = (is_pl & vol_ok).fillna(False)
        df["ph_price"] = np.where(df["vol_ph"], df["high"].shift(swing), np.nan)
        df["pl_price"] = np.where(df["vol_pl"], df["low"].shift(swing), np.nan)
        df["ph_idx"] = np.where(df["vol_ph"], np.arange(len(df)) - swing, np.nan)
        df["pl_idx"] = np.where(df["vol_pl"], np.arange(len(df)) - swing, np.nan)
        return df

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
        dataframe.loc[
            dataframe["ch_valid"] & (dataframe["close"] >= dataframe["ch_mid"]),
            "exit_long",
        ] = 1
        dataframe.loc[
            dataframe["ch_valid"] & (dataframe["close"] <= dataframe["ch_mid"]),
            "exit_short",
        ] = 1
        return dataframe
