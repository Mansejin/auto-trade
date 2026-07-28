from __future__ import annotations

import hashlib
import logging
import time
import urllib.parse
import uuid
from typing import Any

import httpx

logger = logging.getLogger(__name__)

UPBIT_API = "https://api.upbit.com"


class UpbitPublic:
    def __init__(self, timeout: float = 20.0) -> None:
        self._client = httpx.Client(base_url=UPBIT_API, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def candles(self, market: str, timeframe: str, count: int = 200) -> list[dict[str, Any]]:
        path, params = self._candle_request(market, timeframe, count)
        resp = self._client.get(path, params=params)
        resp.raise_for_status()
        data = resp.json()
        return list(reversed(data))

    @staticmethod
    def _candle_request(market: str, timeframe: str, count: int) -> tuple[str, dict[str, Any]]:
        tf = timeframe.strip().lower()
        params: dict[str, Any] = {"market": market, "count": min(count, 200)}
        if tf in {"1d", "d", "day", "days"}:
            return "/v1/candles/days", params
        if tf in {"1w", "w", "week", "weeks"}:
            return "/v1/candles/weeks", params
        if tf.endswith("m") and tf[:-1].isdigit():
            unit = int(tf[:-1])
            if unit not in {1, 3, 5, 10, 15, 30, 60, 240}:
                raise ValueError(f"unsupported minute unit: {unit}")
            return f"/v1/candles/minutes/{unit}", params
        if tf.endswith("h") and tf[:-1].isdigit():
            hours = int(tf[:-1])
            minutes = hours * 60
            if minutes not in {60, 240}:
                raise ValueError(f"unsupported hour timeframe: {tf}")
            return f"/v1/candles/minutes/{minutes}", params
        raise ValueError(f"unsupported timeframe: {timeframe}")


class UpbitPrivate:
    """Authenticated Upbit client for live orders. Used only when PAPER=false."""

    def __init__(self, access_key: str, secret_key: str, timeout: float = 20.0) -> None:
        import jwt  # noqa: PLC0415

        self.access_key = access_key
        self.secret_key = secret_key
        self._jwt = jwt
        self._client = httpx.Client(base_url=UPBIT_API, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def _auth_header(self, query: dict[str, Any] | None = None) -> dict[str, str]:
        payload: dict[str, Any] = {
            "access_key": self.access_key,
            "nonce": str(uuid.uuid4()),
        }
        if query:
            query_string = urllib.parse.urlencode(query)
            payload["query_hash"] = hashlib.sha512(query_string.encode()).hexdigest()
            payload["query_hash_alg"] = "SHA512"
        token = self._jwt.encode(payload, self.secret_key, algorithm="HS256")
        return {"Authorization": f"Bearer {token}"}

    def accounts(self) -> list[dict[str, Any]]:
        headers = self._auth_header()
        resp = self._client.get("/v1/accounts", headers=headers)
        resp.raise_for_status()
        return resp.json()

    def available_balance(self, currency: str) -> float:
        cur = currency.upper()
        for row in self.accounts():
            if str(row.get("currency", "")).upper() == cur:
                return float(row.get("balance") or 0.0)
        return 0.0

    def get_order(self, *, uuid_str: str | None = None, identifier: str | None = None) -> dict[str, Any]:
        if not uuid_str and not identifier:
            raise ValueError("uuid or identifier required")
        query: dict[str, Any] = {}
        if uuid_str:
            query["uuid"] = uuid_str
        if identifier:
            query["identifier"] = identifier
        headers = self._auth_header(query)
        resp = self._client.get("/v1/order", params=query, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def wait_order(
        self,
        *,
        uuid_str: str | None = None,
        identifier: str | None = None,
        timeout_sec: float = 15.0,
    ) -> dict[str, Any]:
        deadline = time.time() + timeout_sec
        last: dict[str, Any] = {}
        while time.time() < deadline:
            try:
                last = self.get_order(uuid_str=uuid_str, identifier=identifier)
                state = str(last.get("state") or "")
                if state in {"done", "cancel"}:
                    return last
            except Exception:
                logger.exception("주문 조회 실패 — 재시도")
            time.sleep(0.7)
        return last

    @staticmethod
    def make_identifier(prefix: str) -> str:
        # Upbit identifier max length 36
        raw = f"{prefix}-{uuid.uuid4().hex}"
        return raw[:36]

    def place_market_buy(
        self,
        market: str,
        krw_amount: float,
        *,
        identifier: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "market": market,
            "side": "bid",
            "ord_type": "price",
            "price": str(int(krw_amount)),
        }
        if identifier:
            body["identifier"] = identifier
        headers = self._auth_header(body)
        resp = self._client.post("/v1/orders", data=body, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def place_market_sell(
        self,
        market: str,
        volume: float,
        *,
        identifier: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "market": market,
            "side": "ask",
            "ord_type": "market",
            "volume": f"{volume:.8f}",
        }
        if identifier:
            body["identifier"] = identifier
        headers = self._auth_header(body)
        resp = self._client.post("/v1/orders", data=body, headers=headers)
        resp.raise_for_status()
        return resp.json()
