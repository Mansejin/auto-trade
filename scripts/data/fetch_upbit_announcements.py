"""Upbit 'trade' category announcements (unofficial API, may be incomplete) -> data/research/upbit_announcements.csv
and KRW listing notices parsed from titles -> data/research/upbit_listing_notices.csv

  python scripts/data/fetch_upbit_announcements.py

Rows: id,first_listed_at_kst,listed_at_kst,title
Listing notices: id,announced_at_kst,ticker,title  (title has '신규 거래지원' or '디지털 자산 추가' and 'KRW')
announced_at = notice publish time (first_listed_at). Trading usually starts hours later; use candles for that.
Recovers delisted KRW listings that the candles API no longer serves. Full refetch each run (~40 requests).
"""
import csv
import re

from _common import OUT, get

URL = "https://api-manager.upbit.com/api/v1/announcements"
LISTING = re.compile(r"신규 거래지원|디지털 자산 추가")
TICKER = re.compile(r"\(([A-Z0-9]{1,15})\)")


def main():
    notes, page = {}, 1
    while True:
        d = get(URL, {"os": "web", "page": page, "per_page": 20, "category": "trade"}, sleep=0.5)
        data = (d or {}).get("data") or {}
        for n in data.get("notices", []):
            notes[n["id"]] = (n["id"], n.get("first_listed_at") or "", n.get("listed_at") or "", n["title"])
        if page >= data.get("total_pages", 0):
            break
        page += 1
    rows = sorted(notes.values(), key=lambda r: r[1])
    with open(OUT / "upbit_announcements.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "first_listed_at_kst", "listed_at_kst", "title"])
        w.writerows(rows)
    lst = []
    for i, first, _, title in rows:
        if LISTING.search(title) and "KRW" in title:
            lst += [(i, first, t, title) for t in TICKER.findall(title) if t != "KRW"]
    with open(OUT / "upbit_listing_notices.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "announced_at_kst", "ticker", "title"])
        w.writerows(lst)
    print(f"announcements: {len(rows)} ({rows[0][1]}..{rows[-1][1]}), KRW listing notices: {len(lst)}")


if __name__ == "__main__":
    main()
