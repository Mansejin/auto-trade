# pragma pylint: disable=missing-docstring, invalid-name
"""Bitget BTCUSDT-M 5m TREND SHORT (true futures).

Entry modes (class attrs):
  cloud_break — close crosses from >= cloud_top to < cloud_bot
  di_cloud    — -DI > +DI AND close < both cloud spans AND ADX>=adx_min
  di_only     — -DI > +DI AND ADX>=adx_min AND RSI < rsi_max

Exit: SL/ROI only.

Bitget UTA one-way: native stopLossPrice/tpsl returns 31008. Exchange SL is a
reduceOnly trigger strategy order (type=trigger) instead. Bot soft SL remains.
"""
from __future__ import annotations

import logging

from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta

logger = logging.getLogger(__name__)

_CAT = "USDT-FUTURES"


def _uta_trigger_body(
    *,
    symbol_id: str,
    side: str,
    qty: str,
    stop: str,
    limit: str,
) -> dict[str, str]:
    """Build Bitget UTA place-strategy-order body for reduce-only stop."""
    return {
        "category": _CAT,
        "symbol": symbol_id,
        "type": "trigger",
        "side": side,
        "reduceOnly": "yes",
        "qty": qty,
        "triggerOrderType": "limit",
        "triggerBy": "mark",
        "triggerPrice": stop,
        "triggerOrderPrice": limit,
    }


# ponytail: ceiling = body shape only; upgrade if Bitget adds one-way type=tpsl that works.
assert _uta_trigger_body(
    symbol_id="BTCUSDT", side="buy", qty="0.0001", stop="66430.5", limit="66500"
)["type"] == "trigger"


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
        """UTA: ignore Classic margin 40085; route exchange SL via trigger orders."""
        exch = None
        for attr in ("_exchange", "exchange"):
            exch = getattr(self.dp, attr, None)
            if exch is not None:
                break
        if exch is None or getattr(exch, "_uta_sl_patched", False):
            return
        api = getattr(exch, "_api", None)
        if api is None or not callable(
            getattr(api, "privateUtaPostV3TradePlaceStrategyOrder", None)
        ):
            return

        orig_margin = getattr(exch, "set_margin_mode", None)
        if callable(orig_margin):

            def _set_margin_mode(pair, margin_mode, accept_fail=False, params=None):
                try:
                    return orig_margin(pair, margin_mode, accept_fail, params)
                except Exception as e:
                    msg = str(e)
                    if (
                        "40085" in msg
                        or "Unified Account" in msg
                        or "Classic Account API" in msg
                    ):
                        return None
                    if accept_fail:
                        return None
                    raise

            exch.set_margin_mode = _set_margin_mode  # type: ignore[method-assign]

        def _create_stoploss(pair, amount, stop_price, order_types, side, leverage):
            market = api.market(pair)
            stop_s = api.price_to_precision(pair, stop_price)
            # buy stop: limit slightly above trigger; sell stop: slightly below
            limit_px = (
                float(stop_price) * 1.002 if side == "buy" else float(stop_price) * 0.998
            )
            limit_s = api.price_to_precision(pair, limit_px)
            qty = api.amount_to_precision(pair, amount)
            body = _uta_trigger_body(
                symbol_id=market["id"],
                side=side,
                qty=qty,
                stop=stop_s,
                limit=limit_s,
            )
            res = api.privateUtaPostV3TradePlaceStrategyOrder(body)
            oid = (res.get("data") or {}).get("orderId")
            if not oid:
                raise RuntimeError(f"UTA trigger stoploss missing orderId: {res}")
            logger.info(
                "UTA trigger stoploss placed %s %s stop=%s limit=%s id=%s",
                pair,
                side,
                stop_s,
                limit_s,
                oid,
            )
            return {
                "id": oid,
                "symbol": pair,
                "type": "stoploss",
                "side": side,
                "amount": float(amount),
                "price": float(limit_s),
                "stopPrice": float(stop_s),
                "stopLossPrice": float(stop_s),
                "status": "open",
                "info": res,
            }

        def _cancel_stoploss_order(order_id: str, pair: str, params: dict | None = None):
            try:
                return api.privateUtaPostV3TradeCancelStrategyOrder(
                    {"category": _CAT, "orderId": order_id}
                )
            except Exception as e:
                # already gone / triggered
                if "25204" in str(e) or "25575" in str(e):
                    return {"id": order_id, "status": "canceled"}
                raise

        def _fetch_stoploss_order(order_id: str, pair: str, params: dict | None = None):
            pending = (
                api.privateUtaGetV3TradeUnfilledStrategyOrders(
                    {"category": _CAT, "type": "trigger"}
                ).get("data")
                or []
            )
            for o in pending:
                if str(o.get("orderId")) == str(order_id):
                    trig = float(o.get("triggerPrice") or 0)
                    return {
                        "id": order_id,
                        "symbol": pair,
                        "type": "stoploss",
                        "status": "open",
                        "stopPrice": trig,
                        "stopLossPrice": trig,
                        "price": float(o.get("triggerOrderPrice") or trig),
                        "info": o,
                    }
            return {
                "id": order_id,
                "symbol": pair,
                "type": "stoploss",
                "status": "closed",
                "info": {},
            }

        def _stoploss_adjust(stop_loss: float, order: dict, side: str) -> bool:
            px = order.get("stopLossPrice") or order.get("stopPrice")
            if px is None:
                return True
            px = float(px)
            return (side == "sell" and stop_loss > px) or (
                side == "buy" and stop_loss < px
            )

        exch.create_stoploss = _create_stoploss  # type: ignore[method-assign]
        exch.cancel_stoploss_order = _cancel_stoploss_order  # type: ignore[method-assign]
        exch.fetch_stoploss_order = _fetch_stoploss_order  # type: ignore[method-assign]
        exch.stoploss_adjust = _stoploss_adjust  # type: ignore[method-assign]
        exch._uta_sl_patched = True
        exch._uta_margin_patched = True
        logger.info("TrendShortV1: UTA margin+trigger-stoploss patches armed")

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
