#!/usr/bin/env python3
"""Card upbit-listing-fade (frozen 2026-10-08), encoded as-is.

Listing day D (KST): Upbit KRW first daily candle date (09:00 KST open, so = KST listing day for listings after 09:00),
or the KST date of the KRW listing notice when the market no longer exists (notice-only rows).
Eligible: D >= 2020-01-01 and Binance USDT-M perp first daily bar < D (perp already existed).
Entry: short at perp open D+1 (UTC 00:00), exit at open D+8 (7 days), 1x, loss capped at -100%.
Funding: short receives rate for settlements in (entry, exit], scaled by price/entry (fixed qty).
Costs round trip: base 0.1% fee + 10bps slip; x2 (card) 0.2% fee + 20bps slip.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from bt_cards_common import N_RANDOM, d, daily_bars, halves, pct_rank, rng, rows, summarize, write_json

SLUG = "upbit-listing-fade"
DELAY, HOLD = 1, 7
COST = {"base": 0.002, "x2": 0.004}
START, OOS0, END = date(2020, 1, 1), date(2023, 7, 1), date(2026, 9, 30)


def main():
    pm = list(rows("listing_perp_map"))
    perp = daily_bars("binance_perp_listing_1d")
    btc = {d(r["date_utc"]): float(r["open"]) for r in rows("binance_perp_1d") if r["symbol"] == "BTCUSDT"}
    fund: dict = {}
    for r in rows("funding_alts"):
        t = datetime.fromisoformat(r["funding_time_utc"].replace("Z", "+00:00"))
        fund.setdefault(r["symbol"], []).append((t, float(r["funding_rate"])))

    def short_ret(sym: str, e: date) -> float | None:
        b, x = perp.get(sym, {}), e + timedelta(HOLD)
        if e not in b or x not in b:
            return None
        p0 = b[e][0]
        t0 = datetime(e.year, e.month, e.day, tzinfo=timezone.utc)
        t1 = t0 + timedelta(HOLD)
        f = sum(r * b.get(t.date(), b[e])[0] / p0 for t, r in fund.get(sym, []) if t0 < t <= t1)
        return max(-1.0, -(b[x][0] / p0 - 1)) + f

    events, skipped = [], {"no_perp": 0, "perp_after_listing": 0, "before_2020_or_after_end": 0, "no_bars": 0}
    for r in pm:
        D = d(r["upbit_first_date_utc"]) if r["upbit_first_date_utc"] else d(r["notice_kst"])
        if not (START <= D <= END - timedelta(DELAY + HOLD)):
            skipped["before_2020_or_after_end"] += 1
            continue
        sym = r["perp_symbol"]
        if not sym or sym not in perp:
            skipped["no_perp"] += 1
            continue
        if min(perp[sym]) >= D:
            skipped["perp_after_listing"] += 1
            continue
        e = D + timedelta(DELAY)
        g = short_ret(sym, e)
        b0 = btc.get(e), btc.get(e + timedelta(HOLD))
        if g is None or None in b0:
            skipped["no_bars"] += 1
            continue
        events.append({"ticker": r["ticker"], "source": r["source"], "listing": D, "entry": e, "sym": sym,
                       "gross": g, "btc_short": -(b0[1] / b0[0] - 1)})
    events.sort(key=lambda x: x["entry"])
    oos = [x for x in events if x["listing"] >= OOS0]
    tr = [x for x in events if x["listing"] < OOS0]
    h1, h2 = halves(oos, lambda x: x["listing"])
    st = lambda ev, c: summarize([x["gross"] - c for x in ev])  # noqa: E731
    res = {"skipped": skipped, "n_events": len(events), "by_source": {}}
    for s in ("first", "first+notice", "notice"):
        res["by_source"][s] = sum(x["source"] == s for x in events)
    for k, ev in (("full", events), ("train", tr), ("oos", oos), ("oos_h1", h1), ("oos_h2", h2)):
        res[k] = {"base": st(ev, COST["base"]), "x2": st(ev, COST["x2"])}
    res["oos_excess_vs_btc_short_x2_mean_pct"] = round(sum(x["gross"] - COST["x2"] - x["btc_short"] for x in oos) / len(oos) * 100, 3) if oos else None
    res["oos_btc_short_mean_pct"] = round(sum(x["btc_short"] for x in oos) / len(oos) * 100, 3) if oos else None
    res["oos_tail_losses_gt_40pct"] = sum(x["gross"] - COST["x2"] < -0.40 for x in oos)
    # events overlap (several listings per week), so all-in sequential compounding is not a tradable curve;
    # fixed-stake view: sum of net returns, median, mean without the 5 best events, worst 5.
    net = sorted(x["gross"] - COST["x2"] for x in oos)
    res["oos_x2_fixed_stake"] = {"sum_pct": round(sum(net) * 100, 1), "median_pct": round(net[len(net) // 2] * 100, 2),
                                 "mean_ex_top5_pct": round(sum(net[:-5]) / (len(net) - 5) * 100, 3),
                                 "worst5_pct": [round(v * 100, 1) for v in net[:5]], "best5_pct": [round(v * 100, 1) for v in net[-5:]]}
    by_year: dict = {}
    for x in events:
        by_year.setdefault(x["listing"].year, []).append(x["gross"] - COST["x2"])
    res["by_year_x2"] = {y: {"n": len(v), "mean_pct": round(sum(v) / len(v) * 100, 2)} for y, v in sorted(by_year.items())}
    # notice-only events = KRW markets later delisted (only recoverable from 2022+ notices)
    res["oos_notice_only_events"] = sum(x["source"] == "notice" for x in oos)
    res["oos_events_from_notice_era"] = sum(x["listing"] >= date(2022, 1, 11) for x in oos)

    # random: same coin, random 7-day short with entry anywhere in its perp history up to END
    R = rng()
    pools = {}
    for x in oos:
        s = x["sym"]
        if s not in pools:
            pools[s] = [e for e in sorted(perp[s]) if e <= END - timedelta(HOLD) and e + timedelta(HOLD) in perp[s]]
    dist = []
    for _ in range(N_RANDOM):
        vals = []
        for x in oos:
            g = short_ret(x["sym"], R.choice(pools[x["sym"]]))
            vals.append((g if g is not None else 0.0) - COST["x2"])
        dist.append(sum(vals) / len(vals))
    actual = sum(x["gross"] - COST["x2"] for x in oos) / len(oos) if oos else 0.0
    res["oos_random_pct_x2"] = pct_rank(actual, dist)
    res["random_p95_mean_pct"] = round(sorted(dist)[int(0.95 * N_RANDOM)] * 100, 3)
    res["events"] = [{k: (str(v) if isinstance(v, date) else (round(v, 5) if isinstance(v, float) else v)) for k, v in x.items()} for x in events]

    o, why = res["oos"]["x2"], []
    if o.get("n", 0) < 30:
        why.append(f"OOS events {o.get('n', 0)} < 30 -> INCONCLUSIVE")
    else:
        if (o["pf"] or 0) < 1.1:
            why.append(f"OOS PF x2 {o['pf']} < 1.1")
        if res["oos_random_pct_x2"] < 95:
            why.append(f"random pct {res['oos_random_pct_x2']} < 95")
        if res["oos_excess_vs_btc_short_x2_mean_pct"] <= 0:
            why.append("excess vs BTC 7d short <= 0")
    res["verdict"] = "INCONCLUSIVE" if o.get("n", 0) < 30 else ("KILL" if why else "SURVIVE")
    res["reasons"] = why
    path = write_json(SLUG, res)
    for k in ("skipped", "n_events", "by_source", "full", "train", "oos", "oos_h1", "oos_h2", "oos_excess_vs_btc_short_x2_mean_pct",
              "oos_btc_short_mean_pct", "oos_tail_losses_gt_40pct", "oos_x2_fixed_stake", "by_year_x2", "oos_notice_only_events", "oos_events_from_notice_era",
              "oos_random_pct_x2", "random_p95_mean_pct", "verdict", "reasons"):
        print(k, res[k])
    print(path)


if __name__ == "__main__":
    main()
