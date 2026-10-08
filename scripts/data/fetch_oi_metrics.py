"""Binance USDT-M open interest, daily snapshot from data.binance.vision 5m metrics -> data/research/<out>.csv

  python scripts/data/fetch_oi_metrics.py                       # BTC/ETH/SOL -> binance_oi_1d.csv
  python scripts/data/fetch_oi_metrics.py --symbols XRPUSDT --out binance_oi_1d

Source: data/futures/um/daily/metrics/<SYM>/<SYM>-metrics-YYYY-MM-DD.zip (5m rows).
Vision create_time is 5 min EARLIER than REST /futures/data/openInterestHist timestamp for the same value
(checked 2026-10-01: vision 23:55 row == REST 00:00). We use snap_time = create_time + 5 min (REST stamp).
Daily rule (point-in-time): OI for date D = last row with snap_time <= D 00:00:00 UTC
(normally REST 00:00 snapshot = last row of file D-1; if missing, the latest earlier row).
  oi / oi_value          : that snapshot. snap_time_utc / stale_min say which row was used.
  oi_pre / oi_value_pre  : the row before it (~23:55), conservative variant if 00:00 latency matters.
  rows_src               : distinct non-zero 5m rows in the source file D-1 (288 = complete), quality flag only.
Missing file D-1 -> no row for D (gap). Resumable per symbol.
"""
import argparse
import csv
import io
import time
import zipfile
from datetime import datetime, timedelta, timezone

import httpx

from _common import OUT, _client, append_rows, last_by_key, read_rows
from fetch_binance_klines import VISION, s3_list

HEADER = ["symbol", "date_utc", "open_time_ms", "snap_time_utc", "stale_min", "oi", "oi_value",
          "pre_time_utc", "oi_pre", "oi_value_pre", "rows_src"]
LAG = timedelta(minutes=5)


def ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def file_rows(key):
    """sorted [(snap_time, oi, oi_value)] or None if the file is missing."""
    for i in range(5):
        try:
            r = _client.get(f"{VISION}/{key}")
            if r.status_code < 500 and r.status_code != 429:
                break
        except httpx.HTTPError:
            pass
        time.sleep(2 ** (i + 1))
    time.sleep(0.05)
    if r.status_code != 200:
        return None
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        rows = {(x[0], x[2], x[3]) for x in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8"))
                if x and x[0][:1].isdigit() and x[2] and float(x[2]) > 0}  # 2020-21 files repeat rows; some rows are 0
    return sorted((ts(t) + LAG, oi, v) for t, oi, v in rows)


def fdate(key):
    return ts(key[-14:-4] + " 00:00:00")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="BTCUSDT,ETHUSDT,SOLUSDT")
    ap.add_argument("--out", default="binance_oi_1d")
    a = ap.parse_args()
    path = OUT / f"{a.out}.csv"
    last = last_by_key(path, ["symbol"], "open_time_ms")
    for sym in a.symbols.split(","):
        pre_key = f"data/futures/um/daily/metrics/{sym}/{sym}-metrics-"
        keys = sorted(k for k in s3_list(f"data/futures/um/daily/metrics/{sym}/") if k.endswith(".zip"))
        done = last.get((sym,), -1)
        todo = [k for k in keys if (fdate(k) + timedelta(days=1)).timestamp() * 1000 > done]
        tail = []
        if todo and done >= 0:  # resume: seed tail from the file before the first todo
            tail = (file_rows(f"{pre_key}{fdate(todo[0]) - timedelta(days=1):%Y-%m-%d}.zip") or [])[-2:]
        out = []
        for i, k in enumerate(todo, 1):
            d0 = fdate(k) + timedelta(days=1)
            rows = file_rows(k)
            if rows is not None:
                tail = (tail + [r for r in rows if r[0] <= d0])[-2:]
                if tail:
                    at, pre = tail[-1], (tail[-2] if len(tail) > 1 else None)
                    out.append((sym, f"{d0:%Y-%m-%d}", int(d0.timestamp() * 1000), iso(at[0]),
                                int((d0 - at[0]).total_seconds() // 60), at[1], at[2],
                                iso(pre[0]) if pre else "", pre[1] if pre else "", pre[2] if pre else "",
                                len(rows)))
            if i % 200 == 0:
                append_rows(path, HEADER, out)
                out = []
                print(f"{sym}: {i}/{len(todo)}", flush=True)
        append_rows(path, HEADER, out)
        print(f"{sym}: done {len(todo)} files", flush=True)
    by = {}
    for r in read_rows(path):
        by.setdefault(r["symbol"], []).append(r)
    for s, rs in by.items():
        stale = sum(int(r["stale_min"]) > 0 for r in rs)
        short = sum(int(r["rows_src"]) < 288 for r in rs)
        print(f"{s}: {len(rs)} days {rs[0]['date_utc']}..{rs[-1]['date_utc']} stale_snap={stale} rows_src<288={short}")


if __name__ == "__main__":
    main()
