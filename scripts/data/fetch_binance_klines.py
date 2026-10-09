"""Binance daily klines (UTC days) -> data/research/<out>.csv

Core (cards: kimchi, funding-carry):
  python scripts/data/fetch_binance_klines.py --market spot --symbols BTCUSDT,ETHUSDT,XRPUSDT --out binance_spot_1d
  python scripts/data/fetch_binance_klines.py --market perp --symbols BTCUSDT,ETHUSDT,XRPUSDT --out binance_perp_1d
Cross-section universe incl. delisted (card: xs-alt-momentum):
  python scripts/data/fetch_binance_klines.py --market spot --universe --out binance_spot_usdt_1d
  Universe = exchangeInfo USDT pairs (TRADING + BREAK) U data.binance.vision spot/monthly/klines/*USDT
  listing, minus leveraged tokens. REST klines still serve BREAK/delisted pairs; symbols REST rejects
  fall back to data.binance.vision monthly 1d zips (spot or futures/um). Symbol list -> binance_spot_usdt_symbols.csv.
Full USDT-M perpetual universe incl. delisted (card: xs-funding-crowding-weekly), chunked (<5 min each):
  python -u scripts/data/fetch_binance_klines.py --market perp --universe --start 2020-01-01 --out binance_um_all_1d --slice 0:100
  python -u scripts/data/fetch_binance_klines.py --market perp --symbols-file data/research/binance_um_symbols.txt --start 2020-01-01 --out binance_um_all_1d --slice 100:200
  Universe = fapi exchangeInfo (PERPETUAL, quote USDT, any status) U vision futures/um/monthly/klines/*USDT,
  minus dated *_YYMMDD. -> binance_um_universe.csv + binance_um_symbols.txt. Then build_um_universe.py.

Rows: symbol,open_time_ms,date_utc,open,high,low,close,volume,quote_volume,trades
Only closed candles are stored. Resumable per symbol.
"""
import argparse
import csv
import io
import re
import zipfile

from _common import DAY_MS, OUT, _client, append_rows, get, iso_to_ms, last_by_key, ms_to_iso, now_ms, read_rows

HEADER = ["symbol", "open_time_ms", "date_utc", "open", "high", "low", "close", "volume", "quote_volume", "trades"]
BASE = {"spot": "https://api.binance.com/api/v3/klines", "perp": "https://fapi.binance.com/fapi/v1/klines"}
VISION = "https://data.binance.vision"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
LEVERAGED = re.compile(r"(UP|DOWN|BULL|BEAR)USDT$")
DATED = re.compile(r"_\d{6}$")
START_MS = iso_to_ms("2017-01-01")
STEP_MS = {"1d": DAY_MS, "1h": 3_600_000, "5m": 300_000}
INTERVAL = "1d"
PAGE_CAP = 5000  # hard stop for paging loops (BTC 5m since 2019 is ~750 pages)


def row(sym, k):
    return (sym, int(k[0]), ms_to_iso(k[0])[:10], k[1], k[2], k[3], k[4], k[5], k[7], k[8])


def rest(market, sym, since):
    """list of rows, or None if the symbol is unknown to REST."""
    out, t, cutoff = [], since, now_ms()
    for _ in range(PAGE_CAP):
        data = get(BASE[market], {"symbol": sym, "interval": INTERVAL, "startTime": t, "limit": 1000}, sleep=0.12)
        if data is None:
            return None if not out and t == since else out
        out += [row(sym, k) for k in data if int(k[6]) < cutoff]
        if len(data) < 1000:
            return out
        t = int(data[-1][0]) + STEP_MS[INTERVAL]
    return out


def s3_list(prefix):
    """Common prefixes / keys under an S3 prefix (paginated)."""
    keys, marker = [], ""
    for _ in range(PAGE_CAP):
        xml = get(S3, {"delimiter": "/", "prefix": prefix, "marker": marker}, sleep=0.1)
        page = re.findall(r"<Prefix>([^<]+)</Prefix>", xml)[1:] + re.findall(r"<Key>([^<]+)</Key>", xml)
        keys += page
        if "<IsTruncated>true</IsTruncated>" not in xml:
            return keys
        marker = re.search(r"<NextMarker>([^<]+)</NextMarker>", xml).group(1)
    return keys


def vision_zips(market, sym, since):
    """Monthly zips from since's month, then daily zips after the last monthly day (delisted mid-month)."""
    root = {"spot": "data/spot", "perp": "data/futures/um"}[market]
    month0 = ms_to_iso(since)[:7]
    out = read_zips(sym, since, [k for k in s3_list(f"{root}/monthly/klines/{sym}/{INTERVAL}/")
                                 if k.endswith(".zip") and k[-11:-4] >= month0])
    day0 = ms_to_iso(max((r[1] for r in out), default=since - STEP_MS[INTERVAL]) + STEP_MS[INTERVAL])[:10]
    return out + read_zips(sym, since, [k for k in s3_list(f"{root}/daily/klines/{sym}/{INTERVAL}/")
                                        if k.endswith(".zip") and k[-14:-4] >= day0])


def read_zips(sym, since, keys):
    out = []
    for key in sorted(keys):
        r = _client.get(f"{VISION}/{key}")
        if r.status_code != 200:
            continue
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for k in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8")):
                if not k or not k[0].isdigit():
                    continue
                if len(k[0]) > 13:  # 2025+ vision files use microseconds
                    k[0], k[6] = int(k[0]) // 1000, int(k[6]) // 1000
                if int(k[0]) >= since:
                    out.append(row(sym, k))
    return out


def universe_um():
    info = get("https://fapi.binance.com/fapi/v1/exchangeInfo", sleep=1)["symbols"]
    # PERPETUAL = crypto (incl. INDEX/PREMARKET); TRADIFI_PERPETUAL = equities/commodities/FX -> filter on underlying_type
    live = {s["symbol"]: s for s in info if s["contractType"].endswith("PERPETUAL") and s["quoteAsset"] == "USDT"}
    vision = {p.rstrip("/").split("/")[-1] for p in s3_list("data/futures/um/monthly/klines/")}
    vision = {s for s in vision if s.endswith("USDT") and not DATED.search(s)}
    syms = sorted(live.keys() | vision)
    with open(OUT / "binance_um_universe.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "source", "exchangeinfo_status", "contract_type", "underlying_type", "onboard_date"])
        for s in syms:
            src = "both" if s in live and s in vision else "exchangeinfo" if s in live else "vision"
            st = live.get(s, {})
            w.writerow([s, src, st.get("status", "ABSENT"), st.get("contractType", ""), st.get("underlyingType", ""),
                        ms_to_iso(st["onboardDate"])[:10] if st else ""])
    with open(OUT / "binance_um_symbols.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(syms) + "\n")
    print(f"universe: {len(syms)} perps ({len(live)} in exchangeInfo, {len(vision - live.keys())} vision-only)", flush=True)
    return syms


def universe():
    info = get("https://api.binance.com/api/v3/exchangeInfo", sleep=1)["symbols"]
    status = {s["symbol"]: s["status"] for s in info if s["quoteAsset"] == "USDT"}
    vision = {p.rstrip("/").split("/")[-1] for p in s3_list("data/spot/monthly/klines/")}
    vision = {s for s in vision if s.endswith("USDT")}
    syms = sorted(s for s in status.keys() | vision if not LEVERAGED.search(s))
    with open(OUT / "binance_spot_usdt_symbols.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "exchangeinfo_status", "in_vision"])
        for s in syms:
            w.writerow([s, status.get(s, "ABSENT"), int(s in vision)])
    print(f"universe: {len(syms)} symbols ({len(vision - status.keys())} vision-only)")
    return syms


def backfill_head(market, syms, start, path):
    root = {"spot": "data/spot", "perp": "data/futures/um"}[market]
    first = {}
    for r in read_rows(path):
        t = int(r["open_time_ms"])
        first[r["symbol"]] = min(t, first.get(r["symbol"], t))
    failed = []
    for i, sym in enumerate(syms, 1):
        if sym not in first:
            continue
        try:
            m0, m1 = ms_to_iso(start)[:7], ms_to_iso(first[sym])[:7]
            keys = [k for k in s3_list(f"{root}/monthly/klines/{sym}/{INTERVAL}/")
                    if k.endswith(".zip") and m0 <= k[-11:-4] <= m1]
            if not any(k[-11:-4] < m1 for k in keys):
                keys = []
            rows = sorted({r for r in read_zips(sym, start, keys) if r[1] < first[sym]}, key=lambda r: r[1])
        except Exception as e:
            failed.append(sym)
            print(f"[{i}/{len(syms)}] {sym}: FAILED {e!r}", flush=True)
            continue
        append_rows(path, HEADER, rows)
        if rows or i % 20 == 0:
            print(f"[{i}/{len(syms)}] {sym}: head +{len(rows)} (vision, before {ms_to_iso(first[sym])[:10]})", flush=True)
    print(f"done {len(syms)} symbols, failed={failed}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", choices=["spot", "perp"], default="spot")
    ap.add_argument("--symbols", default="BTCUSDT,ETHUSDT,XRPUSDT")
    ap.add_argument("--symbols-file")
    ap.add_argument("--universe", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", choices=list(STEP_MS), default="1d")
    ap.add_argument("--start", default="2017-01-01", help="first open date (UTC) for symbols with nothing stored")
    ap.add_argument("--slice", default=":", help="python slice of the symbol list, e.g. 0:100")
    ap.add_argument("--backfill-head", action="store_true",
                    help="add vision rows older than the first stored row (relisted tickers: REST starts at relist)")
    a = ap.parse_args()
    global INTERVAL
    INTERVAL = a.interval
    step = STEP_MS[INTERVAL]
    syms = a.symbols.split(",")
    if a.symbols_file:
        with open(a.symbols_file, encoding="utf-8") as f:
            syms = [s.strip() for s in f if s.strip()]
    if a.universe:
        syms = universe_um() if a.market == "perp" else universe()
    lo, hi = (int(x) if x else None for x in a.slice.split(":"))
    syms = syms[lo:hi]
    start = iso_to_ms(a.start)
    path = OUT / f"{a.out}.csv"
    if a.backfill_head:
        return backfill_head(a.market, syms, start, path)
    last = last_by_key(path, ["symbol"], "open_time_ms")
    failed = []
    for i, sym in enumerate(syms, 1):
        since = last[(sym,)] + step if (sym,) in last else start
        if since > now_ms() - 2 * step:
            continue
        try:
            rows, src = rest(a.market, sym, since), "rest"
            if not rows:  # unknown to REST, or delisted perp REST answers with []
                rows, src = vision_zips(a.market, sym, since), "vision"
        except Exception as e:  # get() gave up or a vision zip failed: skip, re-run resumes
            failed.append(sym)
            print(f"[{i}/{len(syms)}] {sym}: FAILED {e!r}", flush=True)
            continue
        rows = sorted(set(rows or []), key=lambda r: r[1])
        append_rows(path, HEADER, rows)
        if len(syms) <= 40 or i % 20 == 0 or src == "vision" or not rows:
            print(f"[{i}/{len(syms)}] {sym}: +{len(rows)} ({src})", flush=True)
    print(f"done {len(syms)} symbols, failed={failed}", flush=True)


if __name__ == "__main__":
    main()
