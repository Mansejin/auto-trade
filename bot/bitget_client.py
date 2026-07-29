"""Bitget REST v2 client (USDT-M futures + spot wallet for transfers)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

BITGET_API = "https://api.bitget.com"
PRODUCT_USDT_FUTURES = "USDT-FUTURES"


def _ms() -> str:
    return str(int(time.time() * 1000))


class BitgetError(RuntimeError):
    def __init__(self, code: str, msg: str, body: Any = None) -> None:
        super().__init__(f"Bitget {code}: {msg}")
        self.code = code
        self.msg = msg
        self.body = body


class BitgetPublic:
    def __init__(self, timeout: float = 20.0) -> None:
        self._client = httpx.Client(base_url=BITGET_API, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def candles(
        self,
        symbol: str,
        timeframe: str,
        *,
        product_type: str = PRODUCT_USDT_FUTURES,
        limit: int = 200,
    ) -> list[list[str]]:
        """Return oldest→newest candle rows: [ts, o, h, l, c, baseVol, quoteVol]."""
        gran = self._granularity(timeframe)
        params = {
            "symbol": symbol.upper(),
            "productType": product_type,
            "granularity": gran,
            "limit": str(min(limit, 200)),
        }
        data = self._get("/api/v2/mix/market/candles", params)
        rows = list(data or [])
        rows.reverse()  # API is newest-first
        return rows

    def ticker(
        self, symbol: str, *, product_type: str = PRODUCT_USDT_FUTURES
    ) -> dict[str, Any]:
        data = self._get(
            "/api/v2/mix/market/ticker",
            {"symbol": symbol.upper(), "productType": product_type},
        )
        if isinstance(data, list) and data:
            return data[0]
        return data or {}

    def _get(self, path: str, params: dict[str, str]) -> Any:
        resp = self._client.get(path, params=params)
        resp.raise_for_status()
        payload = resp.json()
        if str(payload.get("code")) not in {"00000", "0"}:
            raise BitgetError(str(payload.get("code")), str(payload.get("msg")), payload)
        return payload.get("data")

    @staticmethod
    def _granularity(timeframe: str) -> str:
        tf = timeframe.strip().lower()
        mapping = {
            "1m": "1m",
            "3m": "3m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1H",
            "4h": "4H",
            "6h": "6H",
            "12h": "12H",
            "1d": "1D",
            "d": "1D",
            "day": "1D",
            "1w": "1W",
            "w": "1W",
        }
        if tf in mapping:
            return mapping[tf]
        if tf.endswith("h") and tf[:-1].isdigit():
            hours = int(tf[:-1])
            key = f"{hours}h"
            if key in mapping:
                return mapping[key]
        if tf.endswith("m") and tf[:-1].isdigit():
            return mapping.get(tf, tf)
        raise ValueError(f"unsupported Bitget timeframe: {timeframe}")


class BitgetPrivate:
    """Authenticated Bitget client for futures trading and spot wallet transfers."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        passphrase: str,
        timeout: float = 20.0,
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self._client = httpx.Client(base_url=BITGET_API, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def _sign(self, timestamp: str, method: str, path: str, query: str, body: str) -> str:
        prehash = f"{timestamp}{method.upper()}{path}"
        if query:
            prehash += f"?{query}"
        prehash += body
        digest = hmac.new(
            self.secret_key.encode("utf-8"),
            prehash.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _headers(self, method: str, path: str, query: str, body: str) -> dict[str, str]:
        ts = _ms()
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": self._sign(ts, method, path, query, body),
            "ACCESS-TIMESTAMP": ts,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        query = urlencode({k: str(v) for k, v in (params or {}).items() if v is not None})
        raw_body = json.dumps(body) if body is not None else ""
        headers = self._headers(method, path, query, raw_body)
        url = path if not query else f"{path}?{query}"
        resp = self._client.request(method, url, headers=headers, content=raw_body or None)
        resp.raise_for_status()
        payload = resp.json()
        if str(payload.get("code")) not in {"00000", "0"}:
            raise BitgetError(str(payload.get("code")), str(payload.get("msg")), payload)
        return payload.get("data")

    def futures_account(
        self, symbol: str, *, product_type: str = PRODUCT_USDT_FUTURES, margin_coin: str = "USDT"
    ) -> dict[str, Any]:
        data = self._request(
            "GET",
            "/api/v2/mix/account/account",
            params={
                "symbol": symbol.upper(),
                "productType": product_type,
                "marginCoin": margin_coin,
            },
        )
        return data or {}

    def available_usdt(self, symbol: str = "BTCUSDT") -> float:
        acc = self.futures_account(symbol)
        for key in ("available", "crossedMaxAvailable", "isolatedMaxAvailable", "usdtEquity"):
            if acc.get(key) is not None:
                try:
                    return float(acc[key])
                except (TypeError, ValueError):
                    continue
        return 0.0

    def place_futures_market(
        self,
        *,
        symbol: str,
        size: str,
        side: str,
        trade_side: str,
        product_type: str = PRODUCT_USDT_FUTURES,
        margin_coin: str = "USDT",
        margin_mode: str = "isolated",
        client_oid: str | None = None,
    ) -> dict[str, Any]:
        """side: buy|sell, trade_side: open|close."""
        body = {
            "symbol": symbol.upper(),
            "productType": product_type,
            "marginMode": margin_mode,
            "marginCoin": margin_coin,
            "size": str(size),
            "side": side.lower(),
            "tradeSide": trade_side.lower(),
            "orderType": "market",
            "clientOid": client_oid or uuid.uuid4().hex[:32],
        }
        data = self._request("POST", "/api/v2/mix/order/place-order", body=body)
        return data or {}

    def spot_assets(self, coin: str | None = None) -> list[dict[str, Any]]:
        params = {"coin": coin.upper()} if coin else None
        data = self._request("GET", "/api/v2/spot/account/assets", params=params)
        if isinstance(data, list):
            return data
        return []

    def spot_available(self, coin: str) -> float:
        for row in self.spot_assets(coin):
            if str(row.get("coin", "")).upper() == coin.upper():
                return float(row.get("available") or 0.0)
        return 0.0

    def deposit_address(self, coin: str, chain: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"coin": coin.upper()}
        if chain:
            params["chain"] = chain
        data = self._request("GET", "/api/v2/spot/wallet/deposit-address", params=params)
        return data or {}

    def withdraw(
        self,
        *,
        coin: str,
        amount: str,
        address: str,
        chain: str,
        tag: str | None = None,
        client_oid: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "coin": coin.upper(),
            "transferType": "on_chain",
            "address": address,
            "chain": chain,
            "size": str(amount),
            "clientOid": client_oid or uuid.uuid4().hex[:32],
        }
        if tag:
            body["tag"] = tag
        data = self._request("POST", "/api/v2/spot/wallet/withdrawal", body=body)
        return data or {}
