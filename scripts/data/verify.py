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
         "binance_perp_listing_1d.csv": ("symbol", "date_utc"), "binance_oi_1d.csv": ("symbol", "date_utc"),
         "binance_perp_caution_1d.csv": ("symbol", "date_utc"), "binance_um_all_1d.csv": ("symbol", "date_utc")}


def um_ghosts():
    """build_um_universe flags: no tradable row after last_trade_date, no blank flag (= rebuild needed)."""
    uni = read_rows(OUT / "binance_um_universe.csv")
    last = {r["symbol"]: r["last_trade_date"] for r in uni if r["status"] != "live"}  # live: today's rows are fine
    if not uni:
        return
    for name, col in (("binance_um_all_1d.csv", "open_time_ms"), ("funding_um_all.csv", "funding_time_ms")):
        rows = read_rows(OUT / name)
        held = lambda r: ms_to_iso(int(r[col]) - (col == "funding_time_ms"))[:10]  # funding: day held into settlement
        leak = sum(r["tradable"] == "1" and r["symbol"] in last and held(r) > last[r["symbol"]] for r in rows)
        blank = sum(r.get("tradable") in ("", None) for r in rows)
        ghost = sum(r["tradable"] == "0" for r in rows)
        print(f"{name}: tradable=0 {ghost}, leak after last_trade_date {leak}, unflagged {blank}")
        assert leak == 0 and blank == 0, "re-run scripts/data/build_um_universe.py"


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
    for name in ("funding.csv", "funding_alts.csv", "funding_caution.csv", "funding_um_all.csv"):
        funding(name)
    um_ghosts()
    fx = read_rows(OUT / "usdkrw.csv")
    print(f"usdkrw.csv: rows={len(fx)} {fx[0]['date']}..{fx[-1]['date']} (business days)")
    ls = read_rows(OUT / "upbit_listings.csv")
    post = [r for r in ls if r["first_date_utc"] >= "2020-01-01"]
    print(f"upbit_listings.csv: markets={len(ls)} launch_cohort={sum(r['launch_cohort'] == '1' for r in ls)} first>=2020: {len(post)}")
    n = read_rows(OUT / "upbit_listing_notices.csv")
    print(f"upbit_listing_notices.csv: rows={len(n)} {n[0]['announced_at_kst'][:10]}..{n[-1]['announced_at_kst'][:10]}")


if __name__ == "__main__":
    main()
