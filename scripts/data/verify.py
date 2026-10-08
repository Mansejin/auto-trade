"""Sanity check of data/research CSVs: rows, range, gaps per key.

  python scripts/data/verify.py            # summary per file (+ per key for small files)
Daily gaps = calendar days missing between first and last date for a key.
Funding gaps = intervals > 9h between consecutive settlements.
"""
from collections import defaultdict
from datetime import date

from _common import OUT, ms_to_iso, read_rows

DAILY = {"binance_spot_1d.csv": ("symbol", "date_utc"), "binance_perp_1d.csv": ("symbol", "date_utc"),
         "binance_spot_usdt_1d.csv": ("symbol", "date_utc"), "upbit_krw_1d.csv": ("market", "date_utc"),
         "binance_perp_listing_1d.csv": ("symbol", "date_utc"), "binance_oi_1d.csv": ("symbol", "date_utc")}


def daily(name, key, col):
    by = defaultdict(list)
    for r in read_rows(OUT / name):
        by[r[key]].append(r[col])
    if not by:
        return print(f"{name}: missing")
    tot_rows = sum(map(len, by.values()))
    tot_gap, dup, gappy = 0, 0, []
    for k, v in by.items():
        s = set(v)
        dup += len(v) - len(s)
        span = (date.fromisoformat(max(s)) - date.fromisoformat(min(s))).days + 1
        g = span - len(s)
        tot_gap += g
        if g:
            gappy.append((k, g))
    lo = min(min(v) for v in by.values())
    hi = max(max(v) for v in by.values())
    print(f"{name}: keys={len(by)} rows={tot_rows} {lo}..{hi} gap_days={tot_gap} dup={dup} keys_with_gaps={len(gappy)}")
    if len(by) <= 10:
        for k, v in sorted(by.items()):
            print(f"   {k}: {len(v)} {min(v)}..{max(v)}")
    if gappy:
        print("   worst gaps:", sorted(gappy, key=lambda x: -x[1])[:5])


def funding(name):
    by = defaultdict(list)
    for r in read_rows(OUT / name):
        by[(r["exchange"], r["symbol"])].append(int(r["funding_time_ms"]))
    if not by:
        return print(f"{name}: missing")
    print(f"{name}: keys={len(by)} rows={sum(map(len, by.values()))}")
    for k, v in sorted(by.items())[:10]:
        v.sort()
        gaps = sum(1 for a, b in zip(v, v[1:]) if b - a > 9 * 3_600_000)
        dup = len(v) - len(set(v))
        print(f"   {k}: {len(v)} {ms_to_iso(v[0])}..{ms_to_iso(v[-1])} gaps>9h={gaps} dup={dup}")


def main():
    for name, (k, c) in DAILY.items():
        daily(name, k, c)
    for name in ("funding.csv", "funding_alts.csv"):
        funding(name)
    fx = read_rows(OUT / "usdkrw.csv")
    print(f"usdkrw.csv: rows={len(fx)} {fx[0]['date']}..{fx[-1]['date']} (business days)")
    ls = read_rows(OUT / "upbit_listings.csv")
    post = [r for r in ls if r["first_date_utc"] >= "2020-01-01"]
    print(f"upbit_listings.csv: markets={len(ls)} launch_cohort={sum(r['launch_cohort'] == '1' for r in ls)} first>=2020: {len(post)}")
    n = read_rows(OUT / "upbit_listing_notices.csv")
    print(f"upbit_listing_notices.csv: rows={len(n)} {n[0]['announced_at_kst'][:10]}..{n[-1]['announced_at_kst'][:10]}")


if __name__ == "__main__":
    main()
