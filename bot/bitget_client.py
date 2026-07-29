"""Bitget Unified Trading Account (UTA / API v3) client.

Aligned with Bitget Agent Hub / UTA docs:
https://www.bitget.com/api-doc/uta/intro
https://github.com/Bitget-AI/agent_hub
"""

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
CATEGORY_USDT_FUTURES = "USDT-FUTURES"
CATEGORY_SPOT = "SPOT"


def _ms() -> str:
    return str(int(time.time() * 1000))


class BitgetError(RuntimeError):
    def __init__(self, code: str, msg: str, body: Any = None) -> None:
        super().__init__(f"Bitget {code}: {msg}")
        self.code = code
        self.msg = msg
        self.body = body


class BitgetPublic:
    """Public UTA v3 market data (no API key)."""

    def __init__(self, timeout: float = 20.0, base_url: str = BITGET_API) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def candles(
        self,
        symbol: str,
        timeframe: str,
        *,
        category: str = CATEGORY_USDT_FUTURES,
        limit: int = 200,
    ) -> list[list[str]]:
        """Oldest→newest rows: [ts, open, high, low, close, volume, turnover]."""
        params = {
            "category": category,
            "symbol": symbol.upper(),
            "interval": self._interval(timeframe),
            "limit": str(min(limit, 200)),
        }
        data = self._get("/api/v3/market/candles", params)
        rows = list(data or [])
        # API returns newest-first
        rows.reverse()
        return rows

    def ticker(
        self, symbol: str, *, category: str = CATEGORY_USDT_FUTURES
    ) -> dict[str, Any]:
        data = self._get(
            "/api/v3/market/tickers",
            {"category": category, "symbol": symbol.upper()},
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
    def _interval(timeframe: str) -> str:
        """UTA candle intervals use mixed case (1m, 1H, 1D)."""
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
            return mapping.get(tf, f"{int(tf[:-1])}H")
        if tf.endswith("m") and tf[:-1].isdigit():
            return tf
        raise ValueError(f"unsupported Bitget UTA timeframe: {timeframe}")


class BitgetPrivate:
    """Authenticated UTA v3 client (trade + account + wallet)."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        passphrase: str,
        timeout: float = 20.0,
        base_url: str = BITGET_API,
        *,
        paper_trading: bool = False,
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.paper_trading = paper_trading
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

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
        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": self._sign(ts, method, path, query, body),
            "ACCESS-TIMESTAMP": ts,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US",
        }
        # Demo / paper trading environment (same as agent-mcp --paper-trading)
        if self.paper_trading:
            headers["paptrading"] = "1"
        return headers

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

    # --- Account (UTA) ---

    def account_assets(self) -> dict[str, Any]:
        """GET /api/v3/account/assets — UTA equity + per-coin balances."""
        data = self._request("GET", "/api/v3/account/assets")
        return data or {}

    def available_usdt(self, _symbol: str | None = None) -> float:
        assets = self.account_assets()
        for row in assets.get("assets") or []:
            if str(row.get("coin", "")).upper() == "USDT":
                return float(row.get("available") or 0.0)
        try:
            return float(assets.get("usdtEquity") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def spot_available(self, coin: str) -> float:
        """UTA unified balance for a coin (spot/futures share pool in UTA)."""
        assets = self.account_assets()
        for row in assets.get("assets") or []:
            if str(row.get("coin", "")).upper() == coin.upper():
                return float(row.get("available") or 0.0)
        return 0.0

    # --- Trade (UTA place-order) ---

    def place_order(
        self,
        *,
        category: str,
        symbol: str,
        side: str,
        order_type: str,
        qty: str,
        price: str | None = None,
        pos_side: str | None = None,
        reduce_only: str | None = None,
        client_oid: str | None = None,
        time_in_force: str | None = None,
        margin_mode: str | None = None,
    ) -> dict[str, Any]:
        """POST /api/v3/trade/place-order."""
        body: dict[str, Any] = {
            "category": category,
            "symbol": symbol.upper(),
            "side": side.lower(),
            "orderType": order_type.lower(),
            "qty": str(qty),
            "clientOid": client_oid or uuid.uuid4().hex[:32],
        }
        if price is not None:
            body["price"] = str(price)
        if pos_side:
            body["posSide"] = pos_side.lower()
        if reduce_only:
            body["reduceOnly"] = reduce_only.lower()
        if time_in_force:
            body["timeInForce"] = time_in_force
        if margin_mode:
            mm = margin_mode.lower()
            body["marginMode"] = "crossed" if mm in {"cross", "crossed"} else "isolated"
        data = self._request("POST", "/api/v3/trade/place-order", body=body)
        return data or {}

    def place_futures_market(
        self,
        *,
        symbol: str,
        size: str,
        side: str,
        trade_side: str,
        product_type: str = CATEGORY_USDT_FUTURES,
        margin_coin: str = "USDT",
        margin_mode: str = "isolated",
        client_oid: str | None = None,
    ) -> dict[str, Any]:
        """Compat wrapper used by bitget_runner (maps open/close → UTA place-order)."""
        _ = margin_coin  # UTA size is base coin; margin coin is account-level
        category = product_type or CATEGORY_USDT_FUTURES
        ts = trade_side.lower()
        # Hedge-mode open/close (UTA docs). reduceOnly is lowercase yes/no.
        if ts == "open":
            pos_side = "long" if side.lower() == "buy" else "short"
            reduce_only = "no"
        elif ts == "close":
            # close long → sell; close short → buy
            pos_side = "long" if side.lower() == "sell" else "short"
            reduce_only = "yes"
        else:
            pos_side = "long"
            reduce_only = "no"
        return self.place_order(
            category=category,
            symbol=symbol,
            side=side,
            order_type="market",
            qty=size,
            pos_side=pos_side,
            reduce_only=reduce_only,
            client_oid=client_oid,
            margin_mode=margin_mode,
        )

    # --- Wallet ---

    def deposit_address(self, coin: str, chain: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"coin": coin.upper()}
        if chain:
            params["chain"] = chain
        data = self._request("GET", "/api/v3/account/deposit-address", params=params)
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
        """POST /api/v3/account/withdrawal (on-chain)."""
        body: dict[str, Any] = {
            "coin": coin.upper(),
            "transferType": "on_chain",
            "address": address,
            "chain": chain,
            "size": str(amount),
            "clientOid": client_oid or uuid.uuid4().hex[:32],
            "accountType": "uta",
        }
        if tag:
            body["tag"] = tag
        data = self._request("POST", "/api/v3/account/withdrawal", body=body)
        return data or {}
