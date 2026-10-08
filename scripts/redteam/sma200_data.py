#!/usr/bin/env python3
"""Fetch/cache daily OHLC for the SMA200 red-team. Output: _data/<name>.json = [[date, open, close], ...]."""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.regime_engine_v2 import fetch_days  # noqa: E402

DATA = HERE / "_data"
UA = {"User-Agent": "redteam-sma200", "Accept": "application/json"}


def get(url: str):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.loads(r.read().decode())


def upbit(market: str) -> list:
    if market == "KRW-BTC" and (HERE / "_krwbtc_1d.json").exists():
        c = json.loads((HERE / "_krwbtc_1d.json").read_text(encoding="utf-8"))
    else:
        c = fetch_days(market, want=4000)[:-1]  # drop forming bar
    return [[x["candle_date_time_utc"][:10], x["opening_price"], x["trade_price"]] for x in c]


def binance(symbol: str) -> list:
    out, start = [], 0
    for host in ("https://data-api.binance.vision", "https://api.binance.com"):
        try:
            while True:
                k = get(f"{host}/api/v3/klines?symbol={symbol}&interval=1d&limit=1000&startTime={start}")
                if not k:
                    break
                out += [[datetime.fromtimestamp(r[0] / 1000, timezone.utc).strftime("%Y-%m-%d"), float(r[1]), float(r[4])] for r in k]
                start = k[-1][0] + 1
                if len(k) < 1000:
                    break
                time.sleep(0.2)
            break
        except Exception as e:  # noqa: BLE001
            print("binance host failed", host, e)
            out, start = [], 0
    return out[:-1]


def bitstamp(pair: str = "btcusd") -> list:
    out, start = {}, int(datetime(2011, 9, 1, tzinfo=timezone.utc).timestamp())
    while True:
        d = get(f"https://www.bitstamp.net/api/v2/ohlc/{pair}/?step=86400&limit=1000&start={start}")["data"]["ohlc"]
        if not d:
            break
        for r in d:
            out[datetime.fromtimestamp(int(r["timestamp"]), timezone.utc).strftime("%Y-%m-%d")] = [float(r["open"]), float(r["close"])]
        nxt = int(d[-1]["timestamp"]) + 86400
        if nxt <= start or len(d) < 2:
            break
        start = nxt
        time.sleep(0.3)
    rows = [[k, *v] for k, v in sorted(out.items())]
    return rows[:-1]


SOURCES = {
    "upbit_KRW-BTC": lambda: upbit("KRW-BTC"),
    "upbit_KRW-ETH": lambda: upbit("KRW-ETH"),
    "upbit_KRW-XRP": lambda: upbit("KRW-XRP"),
    "binance_BTCUSDT": lambda: binance("BTCUSDT"),
    "binance_ETHUSDT": lambda: binance("ETHUSDT"),
    "binance_XRPUSDT": lambda: binance("XRPUSDT"),
    "bitstamp_BTCUSD": bitstamp,
}


def load(name: str) -> list:
    p = DATA / f"{name}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    rows = SOURCES[name]()
    DATA.mkdir(exist_ok=True)
    p.write_text(json.dumps(rows), encoding="utf-8")
    return rows


if __name__ == "__main__":
    for n in SOURCES:
        try:
            r = load(n)
            print(n, len(r), r[0][0] if r else None, r[-1][0] if r else None)
        except Exception as e:  # noqa: BLE001
            print(n, "FAILED", e)
