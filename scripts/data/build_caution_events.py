"""Upbit caution (유의 종목) first-designation events -> Binance USDT-M perp map (card: upbit-caution-perp-short).

  python -u scripts/data/fetch_upbit_announcements.py --category all --start-page 1 --max-pages 150   (then 151..)
  python scripts/data/build_caution_events.py
  python -u scripts/data/fetch_binance_klines.py --market perp --symbols-file data/research/caution_perp_symbols.txt --out binance_perp_caution_1d
  python -u scripts/data/fetch_funding.py --exchanges binance --symbols-file data/research/caution_perp_symbols.txt --out funding_caution --slice 0:40
  python scripts/data/build_caution_events.py      # again: fills perp first-candle date / perp_before_notice

Event (card, exact): category '거래', title ~ '유의 ?종목.*지정' and not '해제|연장|기간'; one event per '(TICKER)'
in the title; dropped if the title designates only the BTC/USDT market. A ticker already designated (no later
'유의 종목 ... 해제' / '거래지원 종료' notice naming it, or '전체 ... 해제') is not a new event.
Time = first_listed_at (KST). entry_utc = first 00:00 UTC strictly after it (card: ≥1 min, ≤24 h).
Release/termination titles also accept bare comma-listed tickers ('TT, LSK 유의 종목 해제'), so a later
re-designation counts as new.
Out: upbit_caution_events.csv, caution_perp_symbols.txt
"""
import csv
import re
from datetime import datetime, timedelta, timezone

from _common import OUT, get, read_rows
from fetch_binance_klines import s3_list

DESIG = re.compile(r"유의 ?종목.*지정")
NOT_DESIG = re.compile(r"해제|연장|기간")
RELEASE = re.compile(r"유의 ?종목.*해제")
TERMINATE = re.compile(r"거래 ?지원 종료")
ALL_RELEASE = re.compile(r"전체 (유의 종목 )?해제|종목 전체 해제")
PAREN = re.compile(r"\(([A-Z0-9]{1,15})\)")
BARE = re.compile(r"\b([A-Z][A-Z0-9]{1,14})\b")
MARKET_ONLY = re.compile(r"(BTC|USDT) 마켓")
NOT_TICKER = {"KRW", "BTC", "USDT", "ETH", "ERC"}
KST = timezone(timedelta(hours=9))


def perp_universe():
    info = get("https://fapi.binance.com/fapi/v1/exchangeInfo", sleep=1, tries=4)["symbols"]
    onboard = {s["symbol"]: s.get("onboardDate", "") for s in info
               if s.get("contractType") == "PERPETUAL" and s["quoteAsset"] == "USDT"}
    vision = {p.rstrip("/").split("/")[-1] for p in s3_list("data/futures/um/monthly/klines/")}
    return onboard, {s for s in vision if s.endswith("USDT")}


def main():
    notes = read_rows(OUT / "upbit_announcements_all.csv")
    notes.sort(key=lambda r: (r["first_listed_at_kst"], int(r["id"])))
    active, events, no_ticker, other_cat = set(), [], [], []
    for r in notes:
        title, cat = r["title"], r["category"]
        if cat != "거래" and DESIG.search(title) and not NOT_DESIG.search(title):
            other_cat.append(r)
        elif DESIG.search(title) and not NOT_DESIG.search(title):
            if MARKET_ONLY.search(title) and "KRW" not in title:
                continue
            ticks = [t for t in dict.fromkeys(PAREN.findall(title)) if t not in NOT_TICKER]
            if not ticks:
                no_ticker.append(r)
            for t in ticks:
                if t not in active:
                    events.append((r, t))
                active.add(t)
        elif RELEASE.search(title) or TERMINATE.search(title):
            if ALL_RELEASE.search(title):
                active.clear()
            active -= set(PAREN.findall(title)) | set(BARE.findall(title))

    onboard, vision = perp_universe()
    perps = set(onboard) | vision
    first, live_days = {}, set()
    for k in read_rows(OUT / "binance_perp_caution_1d.csv"):
        first.setdefault(k["symbol"], int(k["open_time_ms"]))
        if float(k["quote_volume"]) > 0:
            live_days.add((k["symbol"], k["date_utc"]))
    rows = []
    for r, t in events:
        at = datetime.fromisoformat(r["first_listed_at_kst"])
        at_ms = int(at.timestamp() * 1000)
        entry = (at.astimezone(timezone.utc) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        if entry - at < timedelta(minutes=1):
            entry += timedelta(days=1)
        sym = next((p for p in (f"{t}USDT", f"1000{t}USDT", f"1000000{t}USDT", f"1M{t}USDT") if p in perps), "")
        f0 = first.get(sym)
        ob = onboard.get(sym, "")
        starts = [x for x in (f0, int(ob) if ob else None) if x is not None]
        before = int(min(starts) < at_ms) if starts else ""
        rows.append((r["id"], r["first_listed_at_kst"], at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     entry.strftime("%Y-%m-%dT%H:%M:%SZ"), t, sym,
                     "" if not sym else ("fapi" if sym in onboard else "vision_only"),
                     "" if not ob else datetime.fromtimestamp(int(ob) / 1000, timezone.utc).strftime("%Y-%m-%d"),
                     "" if f0 is None else datetime.fromtimestamp(f0 / 1000, timezone.utc).strftime("%Y-%m-%d"),
                     before, "" if f0 is None else int((sym, entry.strftime("%Y-%m-%d")) in live_days), r["title"]))
    with open(OUT / "upbit_caution_events.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["notice_id", "announced_at_kst", "announced_at_utc", "entry_utc", "ticker", "perp_symbol",
                    "perp_source", "perp_onboard_utc", "perp_first_candle_utc", "perp_before_notice",
                    "perp_live_at_entry", "title"])
        w.writerows(rows)
    syms = sorted({r[5] for r in rows if r[5]})
    with open(OUT / "caution_perp_symbols.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(syms) + "\n")
    eligible = sum(1 for r in rows if r[9] == 1)
    print(f"events={len(rows)} notices={len({r[0] for r in rows})} with_perp={sum(1 for r in rows if r[5])} "
          f"vision_only={sum(1 for r in rows if r[6] == 'vision_only')} perp_before_notice={eligible} "
          f"before_and_live_at_entry={sum(1 for r in rows if r[9] == 1 and r[10] == 1)} "
          f"perp_symbols={len(syms)}")
    print(f"designation notices with no (TICKER) in title: {len(no_ticker)}")
    for r in no_ticker:
        print(f"  {r['id']} {r['first_listed_at_kst'][:10]} {r['title']}")
    print(f"designation-like titles outside category 거래 (ignored): {len(other_cat)}")
    for r in other_cat:
        print(f"  {r['id']} {r['first_listed_at_kst'][:10]} [{r['category']}] {r['title']}")


if __name__ == "__main__":
    main()
