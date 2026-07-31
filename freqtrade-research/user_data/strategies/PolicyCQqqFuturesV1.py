# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
"""Policy C map on Bitget QQQ/USDT:USDT futures (research only).

Daily regime (engine v2): SMA50/200 + ADX/DI on QQQ 1d (prior closed day).
  bull / transition -> long EMA5/20 cross on 4h (bull-trend-4h-v2) SL10/TP40
  bear               -> short invert of m5-v6 on 1h SL3/TP4.5
  sideways           -> WilliamsR MR long+short on 1h SL2/TP3

Do not hyperopt. Do not mount to LIVE / Upbit Policy C.
"""
from __future__ import annotations

from datetime import datetime

from pandas import DataFrame
import pandas as pd

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta
from technical import qtpylib


def _classify_row(close, s50, s200, adx, pdi, mdi) -> str:
    if pd.isna(s50) or pd.isna(s200) or pd.isna(adx) or pd.isna(pdi) or pd.isna(mdi):
        return "warmup"
    if adx < 20:
        return "sideways"
    if close > s200 and s50 > s200 and pdi >= mdi:
        return "bull"
    if close < s200 and s50 < s200 and close < s50 and mdi > pdi:
        return "bear"
    return "transition"


class PolicyCQqqFuturesV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1h"
    startup_candle_count = 250

    # Widest sleeve SL; custom_stoploss tightens per enter_tag
    stoploss = -0.10
    minimal_roi = {"0": 100}
    trailing_stop = False
    use_exit_signal = True
    use_custom_stoploss = True
    process_only_new_candles = True

    def informative_pairs(self):
        # 4h/1d synthesized from 1h inside populate_indicators (Bitget history short).
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- 1h: bear invert + sideways Williams ---
        dataframe["ema5"] = ta.EMA(dataframe, timeperiod=5)
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["willr"] = ta.WILLR(dataframe, timeperiod=14)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_mid"] = bb["mid"]

        # --- 4h + 1d from 1h resample (Bitget native 1d/4h history too short) ---
        h1 = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="1h")
        h1i = h1.set_index("date").sort_index()
        ohlcv = {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
        htf = h1i.resample("4h").agg(ohlcv).dropna(subset=["close"]).reset_index()
        htf["ema5"] = ta.EMA(htf, timeperiod=5)
        htf["ema20"] = ta.EMA(htf, timeperiod=20)
        dataframe = merge_informative_pair(
            dataframe, htf, self.timeframe, "4h", ffill=True
        )

        d1 = h1i.resample("1D").agg(ohlcv).dropna(subset=["close"]).reset_index()
        d1["sma50"] = ta.SMA(d1, timeperiod=50)
        d1["sma200"] = ta.SMA(d1, timeperiod=200)
        d1["adx_d"] = ta.ADX(d1, timeperiod=14)
        d1["pdi"] = ta.PLUS_DI(d1, timeperiod=14)
        d1["mdi"] = ta.MINUS_DI(d1, timeperiod=14)
        d1["regime_raw"] = [
            _classify_row(c, s50, s200, adx, pdi, mdi)
            for c, s50, s200, adx, pdi, mdi in zip(
                d1["close"], d1["sma50"], d1["sma200"], d1["adx_d"], d1["pdi"], d1["mdi"]
            )
        ]
        d1["regime"] = d1["regime_raw"].shift(1)
        d1 = d1[["date", "regime"]].copy()
        dataframe = merge_informative_pair(
            dataframe, d1, self.timeframe, "1d", ffill=True
        )
        dataframe["regime"] = dataframe["regime_1d"].fillna("warmup")
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bullish = dataframe["regime"].isin(["bull", "transition"])
        bearish = dataframe["regime"] == "bear"
        side = dataframe["regime"] == "sideways"

        # bull-v2 long on 4h EMA cross
        dataframe.loc[
            (
                bullish
                & qtpylib.crossed_above(dataframe["ema5_4h"], dataframe["ema20_4h"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "bull_ema_4h")

        # m5-v6 invert short on 1h
        dataframe.loc[
            (
                bearish
                & qtpylib.crossed_below(dataframe["ema5"], dataframe["ema20"])
                & (dataframe["adx"] > 23)
                & (dataframe["rsi"] > 45)
                & (dataframe["volume"] > 0)
            ),
            ["enter_short", "enter_tag"],
        ] = (1, "bear_m5v6_inv")

        # Williams MR long
        dataframe.loc[
            (
                side
                & (dataframe["adx"] < 20)
                & (dataframe["willr"] < -80)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "side_wr_long")

        # Williams MR short (mirror)
        dataframe.loc[
            (
                side
                & (dataframe["adx"] < 20)
                & (dataframe["willr"] > -20)
                & (dataframe["volume"] > 0)
            ),
            ["enter_short", "enter_tag"],
        ] = (1, "side_wr_short")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Sleeve exits live in custom_exit (tag-aware). Keep columns clean.
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
    ) -> float:
        tag = trade.enter_tag or ""
        if tag.startswith("bull"):
            return -0.10
        if tag.startswith("bear"):
            return -0.03
        if tag.startswith("side"):
            return -0.02
        return -0.10

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ):
        tag = trade.enter_tag or ""
        if tag.startswith("bull") and current_profit >= 0.40:
            return "tp_bull_40"
        if tag.startswith("bear") and current_profit >= 0.045:
            return "tp_bear_4p5"
        if tag.startswith("side") and current_profit >= 0.03:
            return "tp_side_3"

        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None
        row = dataframe.iloc[-1]
        regime = str(row.get("regime", "warmup"))
        if tag.startswith("bull") and regime not in ("bull", "transition"):
            return "regime_flip"
        if tag.startswith("bear") and regime != "bear":
            return "regime_flip"
        if tag.startswith("side") and regime != "sideways":
            return "regime_flip"

        # Signal exits (need prior bar for crosses)
        if len(dataframe) < 2:
            return None
        prev = dataframe.iloc[-2]
        ema5_4h, ema20_4h = row.get("ema5_4h"), row.get("ema20_4h")
        p_ema5_4h, p_ema20_4h = prev.get("ema5_4h"), prev.get("ema20_4h")
        ema5, ema20 = row.get("ema5"), row.get("ema20")
        p_ema5, p_ema20 = prev.get("ema5"), prev.get("ema20")

        if tag.startswith("bull"):
            if (
                pd.notna(ema5_4h)
                and pd.notna(ema20_4h)
                and pd.notna(p_ema5_4h)
                and pd.notna(p_ema20_4h)
                and p_ema5_4h >= p_ema20_4h
                and ema5_4h < ema20_4h
            ):
                return "bull_death_cross_4h"

        if tag.startswith("bear"):
            golden = (
                pd.notna(ema5)
                and pd.notna(ema20)
                and pd.notna(p_ema5)
                and pd.notna(p_ema20)
                and p_ema5 <= p_ema20
                and ema5 > ema20
            )
            if golden or (pd.notna(row.get("rsi")) and row["rsi"] < 30):
                return "bear_cover"

        if tag == "side_wr_long":
            if (
                (pd.notna(row.get("willr")) and row["willr"] > -20)
                or (pd.notna(row.get("bb_mid")) and row["close"] >= row["bb_mid"])
                or (pd.notna(row.get("adx")) and row["adx"] >= 25)
            ):
                return "side_wr_exit"
        if tag == "side_wr_short":
            if (
                (pd.notna(row.get("willr")) and row["willr"] < -80)
                or (pd.notna(row.get("bb_mid")) and row["close"] <= row["bb_mid"])
                or (pd.notna(row.get("adx")) and row["adx"] >= 25)
            ):
                return "side_wr_exit"
        return None
