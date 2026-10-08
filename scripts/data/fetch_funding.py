"""Perp funding history (settlement-time stamped, UTC) -> data/research/<out>.csv

Default: Binance USDT-M + Bybit linear, BTCUSDT/ETHUSDT  -> funding.csv
Alts:    python scripts/data/fetch_funding.py --exchanges binance --symbols-file data/research/listing_perp_symbols.txt --out funding_alts

Rows: exchange,symbol,funding_time_ms,funding_time_utc,funding_rate
funding_time = settlement time (rate applies to positions held at that instant; known at that instant).
Resumable: re-run appends only rows newer than the last stored per (exchange, symbol).
"""
import argparse

from _common import OUT, append_rows, get, iso_to_ms, last_by_key, ms_to_iso, now_ms

HEADER = ["exchange", "symbol", "funding_time_ms", "funding_time_utc", "funding_rate"]
START_MS = iso_to_ms("2019-09-01")


def binance(sym, since):
    rows, t = [], since
    while True:
        # fundingRate limit: 500 req / 5 min / IP -> sleep 0.7s
        data = get("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol": sym, "startTime": t, "limit": 1000}, sleep=0.7)
        if not data:
            break
        rows += [(int(d["fundingTime"]), d["fundingRate"]) for d in data if int(d["fundingTime"]) >= t]
        if len(data) < 1000:
            break
        t = int(data[-1]["fundingTime"]) + 1
    return rows


def bybit(sym, since):
    rows, end = [], now_ms()
    while True:
        data = get("https://api.bybit.com/v5/market/funding/history",
                   {"category": "linear", "symbol": sym, "endTime": end, "limit": 200}, sleep=0.2)
        lst = (data or {}).get("result", {}).get("list", [])
        if not lst:
            break
        batch = [(int(d["fundingRateTimestamp"]), d["fundingRate"]) for d in lst]
        rows += [b for b in batch if b[0] >= since]
        oldest = min(b[0] for b in batch)
        if oldest < since or len(lst) < 200:
            break
        end = oldest - 1
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exchanges", default="binance,bybit")
    ap.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    ap.add_argument("--symbols-file")
    ap.add_argument("--out", default="funding")
    a = ap.parse_args()
    syms = a.symbols.split(",")
    if a.symbols_file:
        with open(a.symbols_file, encoding="utf-8") as f:
            syms = [s.strip() for s in f if s.strip()]
    path = OUT / f"{a.out}.csv"
    last = last_by_key(path, ["exchange", "symbol"], "funding_time_ms")
    fns = {"binance": binance, "bybit": bybit}
    for ex in a.exchanges.split(","):
        for i, sym in enumerate(syms, 1):
            since = last.get((ex, sym), START_MS - 1) + 1
            rows = sorted(set(fns[ex](sym, since)))
            append_rows(path, HEADER, [(ex, sym, t, ms_to_iso(t), r) for t, r in rows])
            print(f"[{i}/{len(syms)}] {ex} {sym}: +{len(rows)}")


if __name__ == "__main__":
    main()
