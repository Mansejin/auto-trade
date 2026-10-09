#!/usr/bin/env python3
"""Card upbit-caution-perp-short (frozen 2026-10-10), encoded as-is.

Events: data/research/upbit_caution_events.csv rows with perp_before_notice=1 AND perp_live_at_entry=1 (card definition,
built by scripts/data/build_caution_events.py; 2020-21 "(N종)" titles and LUNA are excluded by the definition).
Entry: short Binance USDT-M perp at open of entry_utc (first UTC 00:00 after first_listed_at), 1x, loss capped at -100%.
Exit: open of entry+14d. A bar is tradable only if quote_volume > 0 (delisted perps keep flat zero-volume candles);
if the symbol stops trading before the exit day, exit at the close of the last tradable day.
Funding: short receives rate for settlements in (entry, exit], scaled by settlement-day open / entry (fixed qty).
Costs (round trip, subtracted): x2 card = fee 0.10%/side + slip 30bps/side = 0.80%; base = fee 0.05%/side + slip 30bps = 0.70%.
Split by notice date: train < 2023-07-01 <= OOS. Random null: whole OOS calendar shifted by d in ±[30,365] days.

Run: python scripts/bt_upbit_caution_short.py  -> reports/research-cards/upbit-caution-perp-short.json
"""
from __future__ import annotations

import math
import random
from bisect import bisect_right
from datetime import date, datetime, timedelta, timezone

from bt_cards_common import N_RANDOM, SEED, d, halves, pct_rank, rows, summarize, write_json

SLUG = "upbit-caution-perp-short"
HOLD = 14
DAY = timedelta(1)
COST = {"gross": 0.0, "base": 0.007, "x2": 0.008}
OOS0 = date(2023, 7, 1)
NON_ALT = {"BTCUSDT", "USDCUSDT", "XAUTUSDT"}


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def load_bars(names):
    out: dict = {}
    for n in names:
        for r in rows(n):
            out.setdefault(r["symbol"], {})[d(r["date_utc"])] = (float(r["open"]), float(r["close"]), float(r["quote_volume"]),
                                                                 float(r["high"]))
    return out


def load_funding(bars: dict):
    """{symbol: (times, prefix)} with prefix[i] = sum of rate*open(settlement day) for the first i settlements."""
    raw: dict = {}
    for r in rows("funding_caution"):
        t = datetime.fromisoformat(r["funding_time_utc"].replace("Z", "+00:00"))
        raw.setdefault(r["symbol"], []).append((t, float(r["funding_rate"])))
    out = {}
    for s, xs in raw.items():
        xs.sort()
        b, ts, pre = bars.get(s, {}), [], [0.0]
        for t, r in xs:
            o = b.get(t.date())
            ts.append(t)
            pre.append(pre[-1] + (r * o[0] if o else 0.0))
        out[s] = (ts, pre)
    return out


def trade(b: dict, fund, e: date, liq: bool = True):
    """1x short from open of e. Returns (gross, funding, delisted_early, exit_day, liquidated) or None if e not tradable.
    gross + funding is floored at -100% (margin = notional)."""
    if e not in b or b[e][2] <= 0:
        return None
    x = e + HOLD * DAY
    if x in b and b[x][2] > 0 and all(b.get(e + i * DAY, (0, 0, 0))[2] > 0 for i in range(HOLD)):
        px, t_end, early = b[x][0], x, False
    else:
        last = e
        while last + DAY < x and b.get(last + DAY, (0, 0, 0))[2] > 0:
            last += DAY
        if last + DAY == x and x not in b:
            return None  # window runs past data end, not a delisting
        px, t_end, early = b[last][1], last + DAY, True
    p0 = b[e][0]
    if liq:
        # a 1x short loses its whole margin once the daily high reaches 2x entry (funding drain ignored: optimistic for the short)
        dd = e
        while dd < t_end:
            if b[dd][3] >= 2 * p0:
                return -1.0, 0.0, early, dd + DAY, True
            dd += DAY
    t0 = datetime(e.year, e.month, e.day, tzinfo=timezone.utc)
    t1 = datetime(t_end.year, t_end.month, t_end.day, tzinfo=timezone.utc)
    f = 0.0
    if fund:
        ts, pre = fund
        f = (pre[bisect_right(ts, t1)] - pre[bisect_right(ts, t0)]) / p0
    g = max(-1.0, -(px / p0 - 1))
    return g, max(f, -1.0 - g), early, t_end, False


def stats(ev, c="x2"):
    rs = [x["gross"] + x["fund"] - COST[c] for x in ev]
    s = summarize(rs)
    if rs:
        s["median_pct"] = round(sorted(rs)[len(rs) // 2] * 100, 2) if len(rs) % 2 else round((sorted(rs)[len(rs) // 2 - 1] + sorted(rs)[len(rs) // 2]) / 2 * 100, 2)
        s["sum_pct"] = round(sum(rs) * 100, 1)
    return s


def net(x, c="x2"):
    return x["gross"] + x["fund"] - COST[c]


def main():
    print("loading bars...", flush=True)
    bars = load_bars(["binance_perp_caution_1d", "binance_perp_listing_1d", "binance_perp_1d"])
    fund = load_funding(bars)
    btc = bars["BTCUSDT"]
    print(f"symbols {len(bars)}, funding symbols {len(fund)}", flush=True)

    raw = list(rows("upbit_caution_events"))
    excluded = {"no_perp": 0, "perp_after_notice": 0, "perp_dead_at_entry": []}
    events = []
    for r in raw:
        if not r["perp_symbol"]:
            excluded["no_perp"] += 1
            continue
        if r["perp_before_notice"] != "1":
            excluded["perp_after_notice"] += 1
            continue
        if r["perp_live_at_entry"] != "1":
            excluded["perp_dead_at_entry"].append(r["ticker"])
            continue
        ann = datetime.fromisoformat(r["announced_at_utc"].replace("Z", "+00:00"))
        ent = datetime.fromisoformat(r["entry_utc"].replace("Z", "+00:00"))
        lag = (ent - ann).total_seconds()
        assert 60 <= lag <= 86400 and ent.hour == 0 and ent.minute == 0, (r["ticker"], lag)
        sym, e = r["perp_symbol"], ent.date()
        t = trade(bars[sym], fund.get(sym, []), e)
        assert t is not None, (sym, e)
        g, f, early, t_end, liqd = t
        nl = trade(bars[sym], fund.get(sym), e, liq=False)
        bt = trade(btc, None, e)
        events.append({"ticker": r["ticker"], "sym": sym, "notice": d(r["announced_at_kst"]), "entry": e, "exit": t_end,
                       "lag_h": round(lag / 3600, 2), "gross": g, "fund": f, "delisted_early": early, "liquidated": liqd,
                       "noliq_x2": nl[0] + nl[1] - COST["x2"], "price_short": nl[0], "btc_short": bt[0],
                       "coin_bh": bars[sym][e + HOLD * DAY][0] / bars[sym][e][0] - 1 if not early else bars[sym][t_end - DAY][1] / bars[sym][e][0] - 1})
    events.sort(key=lambda x: (x["entry"], x["ticker"]))
    print(f"eligible events {len(events)}", flush=True)
    assert len({(x["sym"], x["entry"]) for x in events}) == len(events)

    # equal-weight alt basket 14d short (no funding, no cost), same delisting rule, event coin excluded
    alts = [s for s in bars if s not in NON_ALT]
    for x in events:
        rs = [trade(bars[s], [], x["entry"]) for s in alts if s != x["sym"]]
        rs = [t[0] for t in rs if t is not None]
        x["basket_short"], x["basket_n"] = mean(rs), len(rs)
    print("basket done", flush=True)

    oos = [x for x in events if x["notice"] >= OOS0]
    tr = [x for x in events if x["notice"] < OOS0]
    h1, h2 = halves(oos, lambda x: x["entry"])
    res: dict = {"card": f"docs/research/cards/{SLUG}.md", "n_raw_rows": len(raw), "excluded": excluded,
                 "excluded_by_definition_note": "2020-02~2021-06 '(N종)' titles (~98 tickers), IOST 2019-11, LUNA 2022-05-11 - not added (card definition)",
                 "n_events": len(events), "n_train": len(tr), "n_oos": len(oos),
                 "delisted_early": [f"{x['ticker']} {x['entry']}->{x['exit']}" for x in events if x["delisted_early"]],
                 "liquidated_2x_high": [f"{x['ticker']} {x['entry']}->{x['exit']}" for x in events if x["liquidated"]]}
    for k, ev in (("full", events), ("train", tr), ("oos", oos), ("oos_h1", h1), ("oos_h2", h2)):
        res[k] = {c: stats(ev, c) for c in COST}
    nl = [x["noliq_x2"] for x in oos]
    res["oos_x2_no_liquidation_info"] = {**summarize(nl), "median_pct": round(sorted(nl)[len(nl) // 2] * 100, 2)}
    res["oos_funding_mean_pct"] = round(mean([x["fund"] for x in oos]) * 100, 3)
    res["oos_funding_median_pct"] = round(sorted(x["fund"] for x in oos)[len(oos) // 2] * 100, 3)
    res["oos_entry_lag_h"] = {"min": min(x["lag_h"] for x in oos), "max": max(x["lag_h"] for x in oos)}

    # benchmarks
    om = mean([net(x) for x in oos])
    res["bench"] = {
        "oos_btc_short_mean_pct": round(mean([x["btc_short"] for x in oos]) * 100, 3),
        "oos_excess_vs_btc_short_x2_mean_pct": round(mean([net(x) - x["btc_short"] for x in oos]) * 100, 3),
        "oos_basket_short_mean_pct": round(mean([x["basket_short"] for x in oos]) * 100, 3),
        "oos_excess_vs_basket_short_x2_mean_pct": round(mean([net(x) - x["basket_short"] for x in oos]) * 100, 3),
        "oos_excess_vs_basket_share_positive": round(mean([net(x) - x["basket_short"] > 0 for x in oos]), 3),
        "basket_size_min_max": [min(x["basket_n"] for x in oos), max(x["basket_n"] for x in oos)],
        "oos_coin_bh_long_mean_pct": round(mean([x["coin_bh"] for x in oos]) * 100, 3),
    }
    res["oos_tail_losses_gt_40pct"] = sum(net(x) < -0.40 for x in oos)
    res["oos_worst_pct"] = round(min(net(x) for x in oos) * 100, 2)

    # year sign (card OOS years: 2023H2, 2024, 2025, 2026)
    yrs: dict = {}
    for x in events:
        k = "2023H2" if x["notice"].year == 2023 and x["notice"] >= OOS0 else str(x["notice"].year)
        yrs.setdefault(k, []).append(x)
    res["by_year_x2"] = {k: stats(v) for k, v in sorted(yrs.items())}
    oos_years = {k: v for k, v in yrs.items() if k in ("2023H2", "2024", "2025", "2026")}
    neg_years = [k for k, v in oos_years.items() if mean([net(x) for x in v]) < 0]
    res["oos_years_negative"] = neg_years
    res["oos_years_with_events"] = sorted(oos_years)

    # concentration
    srt = sorted(oos, key=net, reverse=True)
    tot = sum(net(x) for x in oos)
    by_name: dict = {}
    for x in oos:
        by_name.setdefault(x["ticker"], []).append(net(x))
    names_ranked = sorted(by_name, key=lambda n: -sum(by_name[n]))
    res["concentration"] = {
        "top3": [{"ticker": x["ticker"], "entry": str(x["entry"]), "x2_pct": round(net(x) * 100, 2)} for x in srt[:3]],
        "top3_share_of_sum": round(sum(net(x) for x in srt[:3]) / tot, 3) if tot else None,
        "drop_top1": stats(srt[1:]), "drop_top2": stats(srt[2:]), "drop_top3": stats(srt[3:]),
        "worst2": [{"ticker": x["ticker"], "entry": str(x["entry"]), "x2_pct": round(net(x) * 100, 2)} for x in srt[-2:]],
        "drop_worst1": stats(srt[:-1]), "drop_worst2": stats(srt[:-2]),
        "oos_price_only_short_mean_pct_noliq": round(mean([x["price_short"] for x in oos]) * 100, 3),
        "drop_top2_names": {"names": names_ranked[:2], **stats([x for x in oos if x["ticker"] not in names_ranked[:2]])},
        "leave_one_name_out_min_mean_pct": round(min(mean([net(x) for x in oos if x["ticker"] != n]) for n in by_name) * 100, 3),
        "oos_ex_2026": stats([x for x in oos if x["entry"].year < 2026]),
        "oos_2026_only": stats([x for x in oos if x["entry"].year >= 2026]),
    }
    g: dict = {}
    for x in oos:
        g.setdefault(x["notice"], []).append(net(x))
    cm = [mean(v) for v in g.values()]
    sd = math.sqrt(sum((v - mean(cm)) ** 2 for v in cm) / (len(cm) - 1))
    res["date_cluster_t"] = {"t": round(mean(cm) / sd * math.sqrt(len(cm)), 2), "n_clusters": len(cm)}

    # random null 1 (card): whole OOS calendar shifted by one d in ±[30,365]; same coins, no overlap with own real windows
    real_win = {}
    for x in events:
        real_win.setdefault(x["sym"], []).append(x["entry"])

    def shifted(dd: int):
        vals = []
        for x in oos:
            e = x["entry"] + dd * DAY
            if any(abs((e - w).days) < HOLD for w in real_win[x["sym"]]):
                continue
            t = trade(bars[x["sym"]], fund.get(x["sym"], []), e)
            if t is not None:
                vals.append(t[0] + t[1] - COST["x2"])
        return vals

    def calendar_null(seed: int, signs=(-1, 1)):
        R = random.Random(seed)
        dist, used, redraw = [], [], 0
        while len(dist) < N_RANDOM:
            dd = R.choice(signs) * R.randint(30, 365)
            v = shifted(dd)
            if len(v) < 10:
                redraw += 1
                continue
            dist.append(mean(v))
            used.append(len(v))
        return dist, used, redraw

    print("random calendar shift...", flush=True)
    dist, used, redraw = calendar_null(SEED)
    cal_seeds = [pct_rank(om, calendar_null(SEED + i)[0]) for i in range(1, 5)]
    dneg, uneg, _ = calendar_null(SEED, signs=(-1,))
    res["random_calendar"] = {
        "pct_rank": pct_rank(om, dist), "p99_mean_pct": round(sorted(dist)[int(0.99 * N_RANDOM)] * 100, 3),
        "p50_mean_pct": round(sorted(dist)[N_RANDOM // 2] * 100, 3),
        "events_used_mean": round(mean(used), 1), "events_used_min": min(used), "redraws_lt10": redraw,
        "other_seeds_pct": cal_seeds,
        "negative_shift_only": {"pct_rank": pct_rank(om, dneg), "events_used_mean": round(mean(uneg), 1)},
    }
    print("random independent...", flush=True)
    # random null 2 (info): same coin, independent random entry day in its tradable history (same 14d hold, same count)
    R = random.Random(SEED)
    pools = {s: [e for e in sorted(bars[s]) if trade(bars[s], [], e) is not None] for s in {x["sym"] for x in oos}}
    ind = []
    for _ in range(N_RANDOM):
        vs = []
        for x in oos:
            t = trade(bars[x["sym"]], fund.get(x["sym"], []), R.choice(pools[x["sym"]]))
            vs.append(t[0] + t[1] - COST["x2"])
        ind.append(mean(vs))
    res["random_independent"] = {"pct_rank": pct_rank(om, ind), "p50_mean_pct": round(sorted(ind)[N_RANDOM // 2] * 100, 3)}

    # verdict (card kill list, Binance perp)
    o = res["oos"]["x2"]
    checks = {
        "n_total_ge_30": len(events) >= 30,
        "n_oos_ge_20": len(oos) >= 20,
        "oos_pf_x2_ge_1.1": (o["pf"] or 0) >= 1.1,
        "oos_mean_x2_gt_0": o["mean_pct"] > 0,
        "calendar_random_ge_99": res["random_calendar"]["pct_rank"] >= 99,
        "excess_vs_btc_short_gt_0": res["bench"]["oos_excess_vs_btc_short_x2_mean_pct"] > 0,
        "excess_vs_alt_basket_gt_0": res["bench"]["oos_excess_vs_basket_short_x2_mean_pct"] > 0,
        "oos_negative_years_lt_2": len(neg_years) < 2,
    }
    res["checks"] = checks
    res["tail_label"] = "자동 숏 상품 부적합" if res["oos_tail_losses_gt_40pct"] >= 2 else None
    if not (checks["n_total_ge_30"] and checks["n_oos_ge_20"]):
        res["verdict"] = "INCONCLUSIVE"
    elif not all(checks.values()):
        res["verdict"] = "KILL"
    else:
        res["verdict"] = "SURVIVE"
    res["events"] = [{k: (str(v) if isinstance(v, date) else (round(v, 5) if isinstance(v, float) else v)) for k, v in x.items()}
                     | {"x2": round(net(x), 5)} for x in events]
    path = write_json(SLUG, res)
    for k, v in res.items():
        if k != "events":
            print(k, v)
    for x in res["events"]:
        print(x["entry"], x["ticker"], x["sym"], "x2", x["x2"], "fund", x["fund"], "btc", x["btc_short"],
              "bsk", x["basket_short"], "early" if x["delisted_early"] else "", "LIQ" if x["liquidated"] else "")
    print(path)


if __name__ == "__main__":
    main()
