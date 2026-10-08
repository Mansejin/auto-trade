"""USD/KRW daily (ECB reference, business days only) from frankfurter.app -> data/research/usdkrw.csv

  python scripts/data/fetch_usdkrw.py

Rows: date,usdkrw. ECB publishes ~16:00 CET; weekends/TARGET holidays absent (forward-fill at use time,
never back-fill). Full refetch each run (one request per year, cheap).
"""
import csv
from datetime import date

from _common import OUT, get


def main():
    rates = {}
    for y in range(2017, date.today().year + 1):
        d = get(f"https://api.frankfurter.app/{y}-01-01..{y}-12-31", {"from": "USD", "to": "KRW"}, sleep=0.5)
        rates.update({k: v["KRW"] for k, v in d["rates"].items() if k.startswith(str(y))})
    with open(OUT / "usdkrw.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "usdkrw"])
        w.writerows(sorted(rates.items()))
    print(f"usdkrw: {len(rates)} rows {min(rates)}..{max(rates)}")


if __name__ == "__main__":
    main()
