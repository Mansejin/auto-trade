"""Upbit announcements (unofficial API, may be incomplete).

  python scripts/data/fetch_upbit_announcements.py                  # category=trade (default)
  python -u scripts/data/fetch_upbit_announcements.py --category all --start-page 1 --max-pages 150
  python -u scripts/data/fetch_upbit_announcements.py --category all --start-page 151 --max-pages 150

trade -> upbit_announcements.csv (id,first_listed_at_kst,listed_at_kst,title)
         + upbit_listing_notices.csv (id,announced_at_kst,ticker,title; '신규 거래지원'/'디지털 자산 추가' + 'KRW')
all   -> upbit_announcements_all.csv (id,first_listed_at_kst,listed_at_kst,category,title), ~294 pages.
announced_at = notice publish time (first_listed_at); listed_at is the last-edit time.
Rows are merged by id into the existing CSV, so chunked runs (--start-page/--max-pages) resume. Newer notices push
older ones to later pages, so chunks can overlap but do not skip.
"""
import argparse
import csv
import re

from _common import OUT, get, read_rows

URL = "https://api-manager.upbit.com/api/v1/announcements"
LISTING = re.compile(r"신규 거래지원|디지털 자산 추가")
TICKER = re.compile(r"\(([A-Z0-9]{1,15})\)")
PAGE_CAP = 400


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="trade")
    ap.add_argument("--start-page", type=int, default=1)
    ap.add_argument("--max-pages", type=int, default=PAGE_CAP)
    a = ap.parse_args()
    cols = ["id", "first_listed_at_kst", "listed_at_kst"] + (["category"] if a.category == "all" else []) + ["title"]
    path = OUT / ("upbit_announcements_all.csv" if a.category == "all" else "upbit_announcements.csv")
    notes = {int(r["id"]): tuple(r[c] for c in cols) for r in read_rows(path)}
    page, last = a.start_page, a.start_page + min(a.max_pages, PAGE_CAP) - 1
    while page <= last:
        d = get(URL, {"os": "web", "page": page, "per_page": 20, "category": a.category}, sleep=0.5, tries=4)
        data = (d or {}).get("data") or {}
        for n in data.get("notices", []) + (data.get("fixed_notices") or []):
            n = {**n, "first_listed_at_kst": n.get("first_listed_at") or "", "listed_at_kst": n.get("listed_at") or ""}
            notes[n["id"]] = tuple(n.get(c) or "" for c in cols)
        total = data.get("total_pages", 0)
        if page % 20 == 0:
            print(f"page {page}/{total}: {len(notes)} notices", flush=True)
        if page >= total:
            break
        page += 1
    rows = sorted(notes.values(), key=lambda r: (r[1], int(r[0])))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    print(f"{path.name}: {len(rows)} ({rows[0][1]}..{rows[-1][1]}), stopped at page {page}", flush=True)
    if a.category != "trade":
        return
    lst = []
    for i, first, _, title in rows:
        if LISTING.search(title) and "KRW" in title:
            lst += [(i, first, t, title) for t in TICKER.findall(title) if t != "KRW"]
    with open(OUT / "upbit_listing_notices.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "announced_at_kst", "ticker", "title"])
        w.writerows(lst)
    print(f"KRW listing notices: {len(lst)}")


if __name__ == "__main__":
    main()
