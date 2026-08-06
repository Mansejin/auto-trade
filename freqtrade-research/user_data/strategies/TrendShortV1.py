# pragma pylint: disable=missing-docstring, invalid-name
"""Bitget BTCUSDT-M 5m TREND SHORT (true futures).

Entry modes (class attrs):
  cloud_break — close crosses from >= cloud_top to < cloud_bot
  di_cloud    — -DI > +DI AND close < both cloud spans AND ADX>=adx_min
  di_only     — -DI > +DI AND ADX>=adx_min AND RSI < rsi_max

Exit: SL/ROI only.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta


class TrendShortV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 80

    stoploss = -0.03
    minimal_roi = {"0": 0.09}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    entry_mode = "di_cloud"  # cloud_break | di_cloud | di_only
    adx_min = 15
    rsi_max = 55


    def bot_start(self, **kwargs) -> None:
        """Bitget UTA: Classic set_margin_mode returns 40085 — ignore and continue."""
        exch = None
        for attr in ("_exchange", "exchange"):
            exch = getattr(self.dp, attr, None)
            if exch is not None:
                break
        if exch is None or getattr(exch, "_uta_margin_patched", False):
            return
        orig = getattr(exch, "set_margin_mode", None)
        if not callable(orig):
            return

        def _set_margin_mode(margin_mode, symbol=None, params=None):
            params = dict(params or {})
            params.setdefault("uta", True)
            try:
                return orig(margin_mode, symbol, params)
            except Exception as e:
                msg = str(e)
                if "40085" in msg or "Unified Account" in msg or "Classic Account API" in msg:
                    return {"code": "40085", "ignored": True}
                raise

        exch.set_margin_mode = _set_margin_mode  # type: ignore[method-assign]
        exch._uta_margin_patched = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)
        high, low = dataframe["high"], dataframe["low"]
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2.0
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2.0
        span1 = (tenkan + kijun) / 2.0
        span2 = (high.rolling(52).max() + low.rolling(52).min()) / 2.0
        dataframe["cloud1"] = span1.shift(26)
        dataframe["cloud2"] = span2.shift(26)
        dataframe["cloud_top"] = dataframe[["cloud1", "cloud2"]].max(axis=1)
        dataframe["cloud_bot"] = dataframe[["cloud1", "cloud2"]].min(axis=1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        mode = self.entry_mode
        if mode == "cloud_break":
            cond = (
                (dataframe["close"].shift(1) >= dataframe["cloud_top"].shift(1))
                & (dataframe["close"] < dataframe["cloud_bot"])
            )
        elif mode == "di_cloud":
            cond = (
                (dataframe["minus_di"] > dataframe["plus_di"])
                & (dataframe["adx"] >= self.adx_min)
                & (dataframe["close"] < dataframe["cloud1"])
                & (dataframe["close"] < dataframe["cloud2"])
            )
        else:  # di_only
            cond = (
                (dataframe["minus_di"] > dataframe["plus_di"])
                & (dataframe["adx"] >= self.adx_min)
                & (dataframe["rsi"] < self.rsi_max)
            )

        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe.loc[
            cond & dataframe["cloud1"].notna() & (dataframe["volume"] > 0),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
