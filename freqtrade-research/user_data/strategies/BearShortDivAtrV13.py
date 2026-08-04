# pragma pylint: disable=missing-docstring, invalid-name
"""Bear short div+ATR v13 — Bitget BTCUSDT-M SCALP sleeve research.

Prior BTC short danta v1–v12 falsified (threshold chops / breakdowns).
New axis (not a retune): mirror the Upbit daytrade-edge-10m-div-atr long
edge as a futures short.

Hypothesis: When ATR is rising and 15m prints classic/hidden bearish RSI
divergence at BB upper, while 1h EMA50 < EMA200 (bear structure), price
continues lower more often — short → BB lower (or ROI/SL).

Entry (short only):
  EMA50_1h < EMA200_1h
  AND ATR > ATR[3]
  AND close >= BB upper
  AND (
        (high > high[3] AND rsi < rsi[3])   # classic bearish div
     OR (high < high[3] AND rsi > rsi[3])   # hidden bearish div
      )
Exit:
  close <= BB lower
  OR ROI +2.5% / SL -0.8%

Fee 0.06%. Freeze hypers. CORE Policy C unchanged.
"""
from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta
from technical import qtpylib


class BearShortDivAtrV13(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 220

    stoploss = -0.008
    minimal_roi = {"0": 0.025}
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True

    def informative_pairs(self):
        return [(pair, "1h") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        bb = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lower"] = bb["lower"]
        dataframe["bb_mid"] = bb["mid"]
        dataframe["bb_upper"] = bb["upper"]

        informative = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="1h")
        informative["ema50"] = ta.EMA(informative, timeperiod=50)
        informative["ema200"] = ta.EMA(informative, timeperiod=200)
        dataframe = merge_informative_pair(
            dataframe, informative, self.timeframe, "1h", ffill=True
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        classic = (
            (dataframe["high"] > dataframe["high"].shift(3))
            & (dataframe["rsi"] < dataframe["rsi"].shift(3))
            & (dataframe["close"] >= dataframe["bb_upper"])
        )
        hidden = (
            (dataframe["high"] < dataframe["high"].shift(3))
            & (dataframe["rsi"] > dataframe["rsi"].shift(3))
            & (dataframe["close"] >= dataframe["bb_upper"])
        )
        dataframe.loc[
            (
                (dataframe["ema50_1h"] < dataframe["ema200_1h"])
                & (dataframe["atr"] > dataframe["atr"].shift(3))
                & (classic | hidden)
                & (dataframe["volume"] > 0)
            ),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] <= dataframe["bb_lower"]),
            "exit_short",
        ] = 1
        dataframe["exit_long"] = 0
        return dataframe
