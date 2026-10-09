"""Binance daily klines (UTC days) -> data/research/<out>.csv

Core (cards: kimchi, funding-carry):
  python scripts/data/fetch_binance_klines.py --market spot --symbols BTCUSDT,ETHUSDT,XRPUSDT --out binance_spot_1d
  python scripts/data/fetch_binance_klines.py --market perp --symbols BTCUSDT,ETHUSDT,XRPUSDT --out binance_perp_1d
Cross-section universe incl. delisted (card: xs-alt-momentum):
  python scripts/data/fetch_binance_klines.py --market spot --universe --out binance_spot_usdt_1d
  Universe = exchangeInfo USDT pairs (TRADING + BREAK) U data.binance.vision spot/monthly/klines/*USDT
  listing, minus leveraged tokens. REST klines still serve BREAK/delisted pairs; symbols REST rejects
  fall back to data.binance.vision monthly 1d zips (spot or futures/um). Symbol list -> binance_spot_usdt_symbols.csv.

Rows: symbol,open_time_ms,date_utc,open,high,low,close,volume,quote_volume,trades
Only closed candles are stored. Resumable per symbol.
"""
import argparse
import csv
import io
import re
import zipfile

from _common import DAY_MS, OUT, _client, append_rows, get, iso_to_ms, last_by_key, ms_to_iso, now_ms

HEADER = ["symbol", "open_time_ms", "date_utc", "open", "high", "low", "close", "volume", "quote_volume", "trades"]
BASE = {"spot": "https://api.binance.com/api/v3/klines", "perp": "https://fapi.binance.com/fapi/v1/klines"}
VISION = "https://data.binance.vision"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
LEVERAGED = re.compile(r"(UP|DOWN|BULL|BEAR)USDT$")
START_MS = iso_to_ms("2017-01-01")
STEP_MS = {"1d": DAY_MS, "1h": 3_600_000, "5m": 300_000}
INTERVAL = "1d"


def row(sym, k):
    return (sym, int(k[0]), ms_to_iso(k[0])[:10], k[1], k[2], k[3], k[4], k[5], k[7], k[8])


def rest(market, sym, since):
    """list of rows, or None if the symbol is unknown to REST."""
    out, t, cutoff = [], since, now_ms()
    while True:
        data = get(BASE[market], {"symbol": sym, "interval": INTERVAL, "startTime": t, "limit": 1000}, sleep=0.12)
        if data is None:
            return None if not out and t == since else out
        out += [row(sym, k) for k in data if int(k[6]) < cutoff]
        if len(data) < 1000:
            return out
        t = int(data[-1][0]) + STEP_MS[INTERVAL]


def s3_list(prefix):
    """Common prefixes / keys under an S3 prefix (paginated)."""
    keys, marker = [], ""
    while True:
        xml = get(S3, {"delimiter": "/", "prefix": prefix, "marker": marker}, sleep=0.1)
        page = re.findall(r"<Prefix>([^<]+)</Prefix>", xml)[1:] + re.findall(r"<Key>([^<]+)</Key>", xml)
        keys += page
        if "<IsTruncated>true</IsTruncated>" not in xml:
            return keys
        marker = re.search(r"<NextMarker>([^<]+)</NextMarker>", xml).group(1)


def vision_zips(market, sym, since):
    root = {"spot": "data/spot", "perp": "data/futures/um"}[market]
    out = []
    for key in sorted(k for k in s3_list(f"{root}/monthly/klines/{sym}/{INTERVAL}/") if k.endswith(".zip")):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", choices=["spot", "perp"], default="spot")
    ap.add_argument("--symbols", default="BTCUSDT,ETHUSDT,XRPUSDT")
    ap.add_argument("--symbols-file")
    ap.add_argument("--universe", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", choices=list(STEP_MS), default="1d")
    a = ap.parse_args()
    global INTERVAL
    INTERVAL = a.interval
    step = STEP_MS[INTERVAL]
    syms = a.symbols.split(",")
    if a.symbols_file:
        with open(a.symbols_file, encoding="utf-8") as f:
            syms = [s.strip() for s in f if s.strip()]
    if a.universe:
        syms = universe()
    path = OUT / f"{a.out}.csv"
    last = last_by_key(path, ["symbol"], "open_time_ms")
    for i, sym in enumerate(syms, 1):
        since = last[(sym,)] + step if (sym,) in last else START_MS
        if since > now_ms() - 2 * step:
            continue
        rows, src = rest(a.market, sym, since), "rest"
        if rows is None:
            rows, src = vision_zips(a.market, sym, since), "vision"
        rows = sorted(set(rows or []), key=lambda r: r[1])
        append_rows(path, HEADER, rows)
        print(f"[{i}/{len(syms)}] {sym}: +{len(rows)} ({src})")


if __name__ == "__main__":
    main()
