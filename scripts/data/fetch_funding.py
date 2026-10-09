"""Perp funding history (settlement-time stamped, UTC) -> data/research/<out>.csv

Default: Binance USDT-M + Bybit linear, BTCUSDT/ETHUSDT  -> funding.csv
Alts:    python scripts/data/fetch_funding.py --exchanges binance --symbols-file data/research/listing_perp_symbols.txt --out funding_alts
Chunked: add --slice 0:40, --slice 40:80 ... (each run resumable)
Full USDT-M universe (after fetch_binance_klines --universe wrote binance_um_symbols.txt):
  python -u scripts/data/fetch_funding.py --exchanges binance --symbols-file data/research/binance_um_symbols.txt --start 2020-01-01 --out funding_um_all --slice 0:60

Rows: exchange,symbol,funding_time_ms,funding_time_utc,funding_rate
funding_time = settlement time (rate applies to positions held at that instant; known at that instant).
Binance symbols REST knows nothing about (delisted perps) fall back to data.binance.vision
futures/um/monthly/fundingRate zips (calc_time = settlement time), only when nothing is stored yet.
Resumable: re-run appends only rows newer than the last stored per (exchange, symbol).
"""
import argparse
import csv
import io
import zipfile

from _common import OUT, _client, append_rows, get, iso_to_ms, last_by_key, ms_to_iso, now_ms
from fetch_binance_klines import VISION, s3_list

HEADER = ["exchange", "symbol", "funding_time_ms", "funding_time_utc", "funding_rate"]
PAGE_CAP = 200


def binance(sym, since):
    rows, t = [], since
    for _ in range(PAGE_CAP):
        # fundingRate limit: 500 req / 5 min / IP -> sleep 0.7s
        data = get("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol": sym, "startTime": t, "limit": 1000}, sleep=0.7, tries=4)
        if not data:
            break
        rows += [(int(d["fundingTime"]), d["fundingRate"]) for d in data if int(d["fundingTime"]) >= t]
        if len(data) < 1000:
            break
        t = int(data[-1]["fundingTime"]) + 1
    return rows


def binance_vision(sym):
    rows = []
    for key in sorted(k for k in s3_list(f"data/futures/um/monthly/fundingRate/{sym}/") if k.endswith(".zip")):
        r = _client.get(f"{VISION}/{key}")
        if r.status_code != 200:
            continue
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for k in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8")):
                if k and k[0].isdigit():
                    rows.append((int(k[0]) // 1000 if len(k[0]) > 13 else int(k[0]), k[-1]))
    return rows


def bybit(sym, since):
    rows, end = [], now_ms()
    for _ in range(PAGE_CAP):
        data = get("https://api.bybit.com/v5/market/funding/history",
                   {"category": "linear", "symbol": sym, "endTime": end, "limit": 200}, sleep=0.2, tries=4)
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
    ap.add_argument("--slice", default=":", help="python slice of the symbol list, e.g. 0:40")
    ap.add_argument("--out", default="funding")
    ap.add_argument("--start", default="2019-09-01", help="first settlement date (UTC) for keys with nothing stored")
    a = ap.parse_args()
    start = iso_to_ms(a.start)
    failed = []
    syms = a.symbols.split(",")
    if a.symbols_file:
        with open(a.symbols_file, encoding="utf-8") as f:
            syms = [s.strip() for s in f if s.strip()]
    lo, hi = (int(x) if x else None for x in a.slice.split(":"))
    syms = syms[lo:hi]
    path = OUT / f"{a.out}.csv"
    last = last_by_key(path, ["exchange", "symbol"], "funding_time_ms")
    fns = {"binance": binance, "bybit": bybit}
    for ex in a.exchanges.split(","):
        for i, sym in enumerate(syms, 1):
            since = last.get((ex, sym), start - 1) + 1
            try:
                rows, src = fns[ex](sym, since), "rest"
                if not rows and ex == "binance" and (ex, sym) not in last:
                    rows, src = [x for x in binance_vision(sym) if x[0] >= since], "vision"
            except Exception as e:  # get() gave up or a vision zip failed: skip, re-run resumes
                failed.append((ex, sym))
                print(f"[{i}/{len(syms)}] {ex} {sym}: FAILED {e!r}", flush=True)
                continue
            rows = sorted(set(rows))
            append_rows(path, HEADER, [(ex, sym, t, ms_to_iso(t), r) for t, r in rows])
            if len(syms) <= 40 or i % 20 == 0 or src == "vision" or not rows:
                print(f"[{i}/{len(syms)}] {ex} {sym}: +{len(rows)} ({src})", flush=True)
    print(f"done {len(syms)} symbols, failed={failed}", flush=True)


if __name__ == "__main__":
    main()
