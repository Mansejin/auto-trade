"""Finalize the Binance USDT-M perp universe (card: xs-funding-crowding-weekly). Run after the fetchers:

  python -u scripts/data/build_um_universe.py

Inputs (from fetch_binance_klines --universe / fetch_funding): binance_um_universe.csv, binance_um_all_1d.csv, funding_um_all.csv
- binance_um_all_1d.csv: adds/refreshes column `tradable` = 1 if that day's quote_volume > 0.
  Delisted perps keep getting flat zero-volume candles from REST (ghosts) -> tradable=0.
- funding_um_all.csv: adds/refreshes `tradable` = 1 if the UTC day the position was held into the settlement
  (day of funding_time - 1 ms) has a tradable candle; settlements after the last closed candle use that candle.
  Post-delisting fixed-rate rows -> tradable=0.
- binance_um_universe.csv: adds first_date, last_trade_date (last quote_volume>0 day), kline/funding row counts,
  ghost (tradable=0) counts, zero_vol_days_inside (relist gaps), status = live | delisted | no_data.
Re-run after every incremental fetch (fetchers append rows with blank `tradable`).
"""
import csv
import os
from collections import defaultdict
from datetime import date

from _common import DAY_MS, OUT, read_rows

EPOCH_ORD = date(1970, 1, 1).toordinal()
UNI, KL, FU = OUT / "binance_um_universe.csv", OUT / "binance_um_all_1d.csv", OUT / "funding_um_all.csv"


def rewrite(path, fn):
    """Stream path through fn(header, row) -> row, adding/refreshing a trailing `tradable` column."""
    tmp = path.with_suffix(".tmp")
    with open(path, encoding="utf-8", newline="") as src, open(tmp, "w", encoding="utf-8", newline="") as dst:
        rd, w = csv.reader(src), csv.writer(dst)
        header = next(rd)
        base = header[:-1] if header[-1] == "tradable" else header
        w.writerow(base + ["tradable"])
        idx = {c: i for i, c in enumerate(base)}
        for r in rd:
            r = r[:len(base)]
            w.writerow(r + [fn(idx, r)])
    os.replace(tmp, path)


def main():
    trade_days = defaultdict(set)
    k = defaultdict(lambda: {"rows": 0, "first": None, "last": None})

    def kl(idx, r):
        s, d = r[idx["symbol"]], int(r[idx["open_time_ms"]]) // DAY_MS
        st = k[s]
        st["rows"] += 1
        st["first"] = d if st["first"] is None else min(st["first"], d)
        st["last"] = d if st["last"] is None else max(st["last"], d)
        if float(r[idx["quote_volume"]] or 0) > 0:
            trade_days[s].add(d)
            return 1
        return 0

    rewrite(KL, kl)
    latest = max(st["last"] for st in k.values())
    f = defaultdict(lambda: [0, 0])

    def fu(idx, r):
        s = r[idx["symbol"]]
        d = min((int(r[idx["funding_time_ms"]]) - 1) // DAY_MS, latest)  # today's candle not closed yet
        ok = d in trade_days[s]
        f[s][0] += 1
        f[s][1] += not ok
        return int(ok)

    rewrite(FU, fu)
    iso = lambda d: "" if d is None else str(date.fromordinal(d + EPOCH_ORD))
    uni = read_rows(UNI)
    base = [c for c in uni[0].keys()][:6]
    extra = ["first_date", "last_trade_date", "kline_rows", "ghost_kline_rows", "zero_vol_days_inside",
             "funding_rows", "ghost_funding_rows", "status"]
    counts = defaultdict(int)
    with open(UNI, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out)
        w.writerow(base + extra)
        for u in uni:
            s, td, st = u["symbol"], trade_days[u["symbol"]], k.get(u["symbol"])
            lt = max(td) if td else None
            inside = (lt - min(td) + 1 - len(td)) if td else 0
            ghost_k = (st["rows"] - len(td)) if st else 0
            status = "no_data" if not td else "live" if lt >= latest - 1 else "delisted"
            counts[status] += 1
            w.writerow([u[c] for c in base] + [iso(st["first"]) if st else "", iso(lt), st["rows"] if st else 0, ghost_k,
                                               inside, f[s][0], f[s][1], status])
    print(f"universe {len(uni)}: {dict(counts)}; latest candle {iso(latest)}", flush=True)
    print(f"klines rows {sum(st['rows'] for st in k.values())}, tradable {sum(map(len, trade_days.values()))}", flush=True)
    print(f"funding rows {sum(v[0] for v in f.values())}, ghost {sum(v[1] for v in f.values())}", flush=True)


if __name__ == "__main__":
    main()
