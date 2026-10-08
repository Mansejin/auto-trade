"""Map Upbit KRW listings (2020+) to Binance USDT-M perp symbols (card: upbit-listing-fade).

  python scripts/data/build_listing_perp_map.py
  python scripts/data/fetch_binance_klines.py --market perp --symbols-file data/research/listing_perp_symbols.txt --out binance_perp_listing_1d
  python scripts/data/fetch_funding.py --exchanges binance --symbols-file data/research/listing_perp_symbols.txt --out funding_alts

Inputs: upbit_listings.csv (candle-derived, current markets only) + upbit_listing_notices.csv (incl. delisted).
Perp universe: fapi exchangeInfo (all statuses) U data.binance.vision futures/um monthly klines listing.
Ticker -> perp tries XXXUSDT, 1000XXXUSDT, 1000000XXXUSDT, 1MXXXUSDT.
Out: listing_perp_map.csv (ticker,source,upbit_first_date_utc,notice_kst,perp_symbol), listing_perp_symbols.txt
"""
import csv

from _common import OUT, get, read_rows
from fetch_binance_klines import s3_list


def main():
    info = get("https://fapi.binance.com/fapi/v1/exchangeInfo", sleep=1)["symbols"]
    perps = {s["symbol"] for s in info if s.get("contractType") == "PERPETUAL" and s["quoteAsset"] == "USDT"}
    perps |= {p.rstrip("/").split("/")[-1] for p in s3_list("data/futures/um/monthly/klines/")
              if p.rstrip("/").endswith("USDT")}
    cand = {}
    for r in read_rows(OUT / "upbit_listings.csv"):
        if r["launch_cohort"] == "0" and r["first_date_utc"] >= "2020-01-01":
            cand.setdefault(r["market"][4:], {})["first"] = r["first_date_utc"]
    for r in read_rows(OUT / "upbit_listing_notices.csv"):
        if r["announced_at_kst"] >= "2020-01-01":
            cand.setdefault(r["ticker"], {}).setdefault("notice", r["announced_at_kst"])
    rows = []
    for t, d in sorted(cand.items()):
        sym = next((p for p in (f"{t}USDT", f"1000{t}USDT", f"1000000{t}USDT", f"1M{t}USDT") if p in perps), "")
        src = "+".join(k for k in ("first", "notice") if k in d)
        rows.append((t, src, d.get("first", ""), d.get("notice", ""), sym))
    with open(OUT / "listing_perp_map.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "source", "upbit_first_date_utc", "notice_kst", "perp_symbol"])
        w.writerows(rows)
    syms = sorted({r[4] for r in rows if r[4]})
    with open(OUT / "listing_perp_symbols.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(syms) + "\n")
    print(f"tickers={len(rows)} with_perp={sum(1 for r in rows if r[4])} "
          f"notice_only(delisted?)={sum(1 for r in rows if r[1] == 'notice')} perp_symbols={len(syms)}")


if __name__ == "__main__":
    main()
