"""Upbit KRW daily candles (day = 09:00 KST = 00:00 UTC) -> data/research/upbit_krw_1d.csv
plus derived listing dates -> data/research/upbit_listings.csv

  python scripts/data/fetch_upbit_daily.py                      # all current KRW markets
  python scripts/data/fetch_upbit_daily.py --markets KRW-BTC,KRW-ETH,KRW-XRP

Rows: market,date_utc,open,high,low,close,volume,value_krw   (closed candles only)
Listings: market,first_date_utc,last_date_utc,n_days,missing_days,launch_cohort
  first_date_utc = first daily candle (proxy for KRW listing / trading start).
  launch_cohort=1 when first candle is within 45 days of the earliest market (exchange launch, not a listing event).
Survivorship: delisted markets return 404 from the candles API -> absent here; see fetch_upbit_announcements.py.
Resumable: per market, pages backwards only until already-stored dates.
"""
import argparse
import csv
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from _common import OUT, append_rows, get, read_rows

HEADER = ["market", "date_utc", "open", "high", "low", "close", "volume", "value_krw"]
URL = "https://api.upbit.com/v1/candles/days"


def fetch(market, stop_after):
    """Candles newer than stop_after (YYYY-MM-DD or '') and older than today (UTC)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out, to = [], None
    while True:
        p = {"market": market, "count": 200}
        if to:
            p["to"] = to
        data = get(URL, p, sleep=0.13)  # candle API: 10 req/s
        if not data:
            break
        for c in data:
            d = c["candle_date_time_utc"][:10]
            if stop_after < d < today:
                out.append((market, d, c["opening_price"], c["high_price"], c["low_price"], c["trade_price"],
                            c["candle_acc_trade_volume"], c["candle_acc_trade_price"]))
        oldest = data[-1]["candle_date_time_utc"]
        if len(data) < 200 or oldest[:10] <= stop_after:
            break
        to = oldest + "Z"
    return out


def write_listings(path):
    days = defaultdict(list)
    for r in read_rows(path):
        days[r["market"]].append(r["date_utc"])
    first_all = min(min(v) for v in days.values())
    cutoff = (date.fromisoformat(first_all) + timedelta(days=45)).isoformat()
    with open(OUT / "upbit_listings.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["market", "first_date_utc", "last_date_utc", "n_days", "missing_days", "launch_cohort"])
        for m, v in sorted(days.items(), key=lambda kv: min(kv[1])):
            lo, hi = min(v), max(v)
            span = (date.fromisoformat(hi) - date.fromisoformat(lo)).days + 1
            w.writerow([m, lo, hi, len(set(v)), span - len(set(v)), int(lo <= cutoff)])
    print(f"listings: {len(days)} markets")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--markets")
    a = ap.parse_args()
    if a.markets:
        markets = a.markets.split(",")
    else:
        markets = sorted(m["market"] for m in get("https://api.upbit.com/v1/market/all", {"isDetails": "false"})
                         if m["market"].startswith("KRW-"))
    path = OUT / "upbit_krw_1d.csv"
    last = {}
    for r in read_rows(path):
        last[r["market"]] = max(last.get(r["market"], ""), r["date_utc"])
    for i, m in enumerate(markets, 1):
        rows = sorted(set(fetch(m, last.get(m, ""))), key=lambda r: r[1])
        append_rows(path, HEADER, rows)
        print(f"[{i}/{len(markets)}] {m}: +{len(rows)}")
    write_listings(path)


if __name__ == "__main__":
    main()
