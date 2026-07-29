# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
"""RSI+BB scalp with daily regime long/short gate (research).

Same entry as RsiBbScalpLongShortV4, plus Policy-C-style daily regime bias:
  bull       -> long only
  bear       -> short only
  sideways   -> no new entries
  transition -> no new entries

Daily regime from Binance BTCUSDT-M 1d (Bitget 1d history too short for SMA200).
Uses prior completed daily bar only (shift 1) to avoid lookahead.
Do not mount to LIVE / Policy C from this alone.
"""
from __future__ import annotations

from pathlib import Path

from pandas import DataFrame
import pandas as pd

from freqtrade.strategy import IStrategy
import talib.abstract as ta
from technical import qtpylib


class RsiBbScalpRegimeGateV1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "5m"
    startup_candle_count = 40

    stoploss = -0.003
    minimal_roi = {"0": 0.008}
    trailing_stop = False
    use_exit_signal = False
    process_only_new_candles = True

    # Cached daily allow flags: date(UTC) -> (allow_long, allow_short)
    _regime_by_date: dict | None = None

    def _load_regime_map(self) -> dict:
        if self._regime_by_date is not None:
            return self._regime_by_date

        # user_data/data/binance/futures/BTC_USDT_USDT-1d-futures.feather
        root = Path(__file__).resolve().parents[1]  # user_data/
        path = root / "data" / "binance" / "futures" / "BTC_USDT_USDT-1d-futures.feather"
        if not path.exists():
            # fallback: flat futures dir from download-data --data-dir
            path = root / "data" / "futures" / "BTC_USDT_USDT-1d-futures.feather"
        if not path.exists():
            self._regime_by_date = {}
            return self._regime_by_date

        inf = pd.read_feather(path)
        if "date" not in inf.columns:
            raise RuntimeError(f"unexpected columns in {path}: {inf.columns.tolist()}")
        inf = inf.sort_values("date").reset_index(drop=True)
        inf["sma50"] = ta.SMA(inf, timeperiod=50)
        inf["sma200"] = ta.SMA(inf, timeperiod=200)
        inf["adx_d"] = ta.ADX(inf, timeperiod=14)
        inf["pdi"] = ta.PLUS_DI(inf, timeperiod=14)
        inf["mdi"] = ta.MINUS_DI(inf, timeperiod=14)

        # Closed-bar: signal from day T applies to day T+1 session
        sideways = inf["adx_d"] < 20
        bull = (
            (inf["close"] > inf["sma200"])
            & (inf["sma50"] > inf["sma200"])
            & (inf["pdi"] >= inf["mdi"])
            & (~sideways)
        )
        bear = (
            (inf["close"] < inf["sma200"])
            & (inf["sma50"] < inf["sma200"])
            & (inf["close"] < inf["sma50"])
            & (inf["mdi"] > inf["pdi"])
            & (~sideways)
        )
        allow_long = bull.fillna(False)
        allow_short = bear.fillna(False)

        # Map: trading date D uses regime from previous daily bar
        regime: dict = {}
        for i in range(len(inf) - 1):
            next_day = pd.Timestamp(inf.loc[i + 1, "date"]).floor("D")
            # After shift logic: bar i (completed) gates the next calendar day
            regime[next_day] = (
                int(bool(allow_long.iloc[i])),
                int(bool(allow_short.iloc[i])),
            )
        self._regime_by_date = regime
        return regime

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=20, stds=2
        )
        dataframe["bb_lower"] = bollinger["lower"]
        dataframe["bb_middle"] = bollinger["mid"]
        dataframe["bb_upper"] = bollinger["upper"]
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)

        regime = self._load_regime_map()
        dates = pd.to_datetime(dataframe["date"], utc=True).dt.floor("D")
        allow_long = []
        allow_short = []
        # Normalize regime keys to UTC midnight
        norm = {}
        for k, v in regime.items():
            kk = pd.Timestamp(k)
            if kk.tzinfo is None:
                kk = kk.tz_localize("UTC")
            else:
                kk = kk.tz_convert("UTC")
            norm[kk.floor("D")] = v
        for d in dates:
            flags = norm.get(d, (0, 0))
            allow_long.append(flags[0])
            allow_short.append(flags[1])
        dataframe["allow_long_1d"] = allow_long
        dataframe["allow_short_1d"] = allow_short
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] < 25)
                & (dataframe["close"] < dataframe["bb_lower"])
                & (dataframe["adx"] < 30)
                & (dataframe["allow_long_1d"] == 1)
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1

        dataframe.loc[
            (
                (dataframe["rsi"] > 75)
                & (dataframe["close"] > dataframe["bb_upper"])
                & (dataframe["adx"] < 30)
                & (dataframe["allow_short_1d"] == 1)
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
