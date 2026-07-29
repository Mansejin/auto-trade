#!/usr/bin/env python3
"""AE12/AE14 forward collector — OKX + Bitget funding + Upbit orderbook.

Append-only JSONL. No strategy promotion. No threshold mining.
Intended cron: every 10–60 minutes on the bot host.

Venues are logged separately (okx-funding.jsonl vs bitget-funding.jsonl).
Do not pool sources into one event study without a new AE id.

Environment:
  AUTO_TRADE_ROOT  default: repo root (script parents[1])
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("AUTO_TRADE_ROOT", Path(__file__).resolve().parents[1]))
OUT_DIR = ROOT / "reports" / "ae12-collect"
FUNDING_LOG = OUT_DIR / "okx-funding.jsonl"
BITGET_FUNDING_LOG = OUT_DIR / "bitget-funding.jsonl"
ORDERBOOK_LOG = OUT_DIR / "upbit-orderbook.jsonl"
BITGET_API = "https://api.bitget.com"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_json(url: str) -> object:
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "ae12-forward-collect"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def append_jsonl(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _f(x):
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _bitget_payload(raw: object) -> object:
    """Normalize Bitget REST: either bare payload or {code,data,...}."""
    if isinstance(raw, dict) and "data" in raw and "code" in raw:
        return raw.get("data")
    return raw


def collect_funding() -> dict:
    # OKX (Binance often geo-blocked). Spot + next period.
    data = get_json(
        "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP"
    )
    row = (data.get("data") or [None])[0] or {}
    rec = {
        "ts_utc": utc_now(),
        "source": "okx",
        "instId": row.get("instId", "BTC-USDT-SWAP"),
        "fundingRate": _f(row.get("fundingRate")),
        "nextFundingRate": _f(row.get("nextFundingRate")),
        "fundingTime": row.get("fundingTime"),
        "nextFundingTime": row.get("nextFundingTime"),
    }
    append_jsonl(FUNDING_LOG, rec)
    return rec


def collect_bitget_funding(symbol: str = "BTCUSDT") -> dict:
    """Bitget UTA v3 public current fund rate + ticker mark/index (AE14 forward)."""
    fund_raw = get_json(f"{BITGET_API}/api/v3/market/current-fund-rate?symbol={symbol}")
    fund = _bitget_payload(fund_raw)
    if isinstance(fund, list):
        row = fund[0] if fund else {}
    elif isinstance(fund, dict):
        row = fund
    else:
        row = {}

    ticker_raw = get_json(
        f"{BITGET_API}/api/v3/market/tickers?category=USDT-FUTURES&symbol={symbol}"
    )
    ticker = _bitget_payload(ticker_raw)
    if isinstance(ticker, list):
        trow = ticker[0] if ticker else {}
    elif isinstance(ticker, dict):
        trow = ticker
    else:
        trow = {}

    mark = _f(trow.get("markPrice"))
    index = _f(trow.get("indexPrice"))
    basis = None
    if mark is not None and index not in (None, 0):
        basis = mark / index - 1.0
    rec = {
        "ts_utc": utc_now(),
        "source": "bitget",
        "symbol": symbol,
        "fundingRate": _f(row.get("fundingRate")),
        "fundingRateInterval": row.get("fundingRateInterval"),
        "nextUpdate": row.get("nextUpdate"),
        "markPrice": mark,
        "indexPrice": index,
        "basis_mark_index": round(basis, 8) if basis is not None else None,
        "lastPrice": _f(trow.get("lastPrice")),
        "openInterest": _f(trow.get("openInterest")),
    }
    append_jsonl(BITGET_FUNDING_LOG, rec)
    return rec


def collect_orderbook(market: str = "KRW-BTC") -> dict:
    data = get_json(f"https://api.upbit.com/v1/orderbook?markets={market}")
    book = data[0] if isinstance(data, list) and data else {}
    units = book.get("orderbook_units") or []
    bid = float(units[0]["bid_size"]) if units else 0.0
    ask = float(units[0]["ask_size"]) if units else 0.0
    depth_bid = sum(float(u["bid_size"]) for u in units)
    depth_ask = sum(float(u["ask_size"]) for u in units)
    imb = None
    if depth_bid + depth_ask > 0:
        imb = (depth_bid - depth_ask) / (depth_bid + depth_ask)
    rec = {
        "ts_utc": utc_now(),
        "market": market,
        "timestamp": book.get("timestamp"),
        "best_bid_size": bid,
        "best_ask_size": ask,
        "total_bid_size": float(book.get("total_bid_size") or depth_bid),
        "total_ask_size": float(book.get("total_ask_size") or depth_ask),
        "imbalance": round(imb, 6) if imb is not None else None,
        "levels": len(units),
    }
    append_jsonl(ORDERBOOK_LOG, rec)
    return rec


def main() -> None:
    funding = collect_funding()
    time.sleep(0.05)
    bitget = collect_bitget_funding()
    time.sleep(0.05)
    book = collect_orderbook()
    summary = {
        "ts_utc": utc_now(),
        "okx_fundingRate": funding.get("fundingRate"),
        "bitget_fundingRate": bitget.get("fundingRate"),
        "bitget_basis_mark_index": bitget.get("basis_mark_index"),
        "orderbook_imbalance": book.get("imbalance"),
        "funding_log": str(FUNDING_LOG),
        "bitget_funding_log": str(BITGET_FUNDING_LOG),
        "orderbook_log": str(ORDERBOOK_LOG),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
