#!/usr/bin/env python3
"""T-009 red-team of upbit-listing-fade. Does not modify the strategy; re-encodes its event set and attacks it.

Run from repo root: python scripts/redteam/listing_fade_redteam.py  -> scripts/redteam/listing_fade_redteam_out.json
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bt_cards_common import DATA, d, pct_rank, pf  # noqa: E402

OUT = Path(__file__).with_name("listing_fade_redteam_out.json")
HOLD = 7
COST = 0.004  # card x2: 0.2% fee + 20bps slip round trip
START, OOS0, END = date(2020, 1, 1), date(2023, 7, 1), date(2026, 9, 30)
MM = 0.01  # maintenance margin used for liquidation
SEED = 20261008
STABLE = {"USDC", "BUSD", "TUSD", "USDP", "PAX", "DAI", "FDUSD", "USDS", "USDSB", "SUSD", "EUR", "GBP", "AUD", "AEUR",
          "EURI", "USDE", "USD1", "BFUSD", "XUSD", "RLUSD", "PAXG", "WBTC", "WBETH", "BETH", "BTC", "ETH", "UST", "USTC",
          "BKRW", "IDRT", "BIDR", "TRY", "BRL", "RUB", "NGN", "UAH", "ZAR", "PLN", "RON", "ARS", "JPY", "MXN", "COP", "CZK"}


def rows(name):
    with open(DATA / f"{name}.csv", encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f)


def load_bars(name):
    out: dict = defaultdict(dict)
    for r in rows(name):
        out[r["symbol"]][d(r["date_utc"])] = (float(r["open"]), float(r["high"]), float(r["close"]), float(r["quote_volume"] or 0))
    return out


perp = load_bars("binance_perp_listing_1d")
fund: dict = defaultdict(list)
for r in rows("funding_alts"):
    fund[r["symbol"]].append((datetime.fromisoformat(r["funding_time_utc"].replace("Z", "+00:00")), float(r["funding_rate"])))
btc = {d(r["date_utc"]): float(r["open"]) for r in rows("binance_perp_1d") if r["symbol"] == "BTCUSDT"}


def short_ret(sym, e, hold=HOLD, with_funding=True):
    b, x = perp.get(sym, {}), e + timedelta(hold)
    if e not in b or x not in b:
        return None
    p0 = b[e][0]
    t0 = datetime(e.year, e.month, e.day, tzinfo=timezone.utc)
    f = sum(r * b.get(t.date(), b[e])[0] / p0 for t, r in fund.get(sym, []) if t0 < t <= t0 + timedelta(hold)) if with_funding else 0.0
    return max(-1.0, -(b[x][0] / p0 - 1)) + f


# ---- events (same encoding as scripts/bt_upbit_listing_fade.py) ----
events = []
for r in rows("listing_perp_map"):
    D = d(r["upbit_first_date_utc"]) if r["upbit_first_date_utc"] else d(r["notice_kst"])
    if not (START <= D <= END - timedelta(1 + HOLD)):
        continue
    sym = r["perp_symbol"]
    if not sym or sym not in perp or min(perp[sym]) >= D:
        continue
    nt = datetime.fromisoformat(r["notice_kst"]).astimezone(timezone.utc) if r["notice_kst"] else None
    e = D + timedelta(1)
    g = short_ret(sym, e)
    if g is None or e not in btc or e + timedelta(HOLD) not in btc:
        continue
    events.append({"ticker": r["ticker"], "source": r["source"], "D": D, "notice": nt, "sym": sym, "e": e,
                   "perp_first": min(perp[sym]), "gross": g, "net": g - COST, "fund": g - short_ret(sym, e, with_funding=False),
                   "btc_short": -(btc[e + timedelta(HOLD)] / btc[e] - 1)})
events.sort(key=lambda x: x["e"])
oos = [x for x in events if x["D"] >= OOS0]


def st(v):
    v = list(v)
    if not v:
        return {"n": 0}
    s = sorted(v)
    return {"n": len(v), "pf": pf(v), "mean_pct": round(sum(v) / len(v) * 100, 2), "median_pct": round(s[len(s) // 2] * 100, 2),
            "win_pct": round(sum(x > 0 for x in v) / len(v) * 100, 1)}


res: dict = {"reproduce_oos_x2": st(x["net"] for x in oos), "n_full": len(events)}

# ---- 1. timing ----
withn = [x for x in oos if x["notice"]]
hrs = sorted(((datetime(x["e"].year, x["e"].month, x["e"].day, tzinfo=timezone.utc) - x["notice"]).total_seconds() / 3600, x["ticker"]) for x in withn)
res["timing"] = {
    "oos_with_notice": len(withn),
    "hours_notice_to_D1_entry": {"min": round(hrs[0][0], 1), "p10": round(hrs[len(hrs) // 10][0], 1), "median": round(hrs[len(hrs) // 2][0], 1), "max": round(hrs[-1][0], 1)},
    "entry_before_notice": [t for h, t in hrs if h < 0],
    "entry_lt_12h_after_notice": sum(h < 12 for h, _ in hrs),
    "entry_lt_24h_after_notice": sum(h < 24 for h, _ in hrs),
    "first_candle_date_ne_notice_utc_date": [x["ticker"] for x in withn if x["source"] == "first+notice" and x["D"] != x["notice"].date()],
}


def variant(evs, entry_fn):
    out = []
    for x in evs:
        e = entry_fn(x)
        if e is None:
            continue
        g = short_ret(x["sym"], e)
        if g is not None:
            out.append(g - COST)
    return out


t24 = lambda x: (x["notice"] + timedelta(hours=24)).date() + timedelta(1) if x["notice"] else None  # noqa: E731
res["timing"]["notice_subset_D1_baseline"] = st(x["net"] for x in withn)
res["timing"]["notice_subset_notice_plus24h"] = st(variant(withn, t24))
res["timing"]["oos_D2_all"] = st(variant(oos, lambda x: x["D"] + timedelta(2)))
res["timing"]["oos_D3_all"] = st(variant(oos, lambda x: x["D"] + timedelta(3)))
res["timing"]["oos_D0_all_for_reference"] = st(variant(oos, lambda x: x["D"]))

# ---- 2. perp tradability / age ----
buckets = {"<=7d": (0, 7), "8-30d": (8, 30), "31-180d": (31, 180), ">180d": (181, 99999)}
res["perp_age_at_listing"] = {}
for k, (a, b) in buckets.items():
    sub = [x for x in oos if a <= (x["D"] - x["perp_first"]).days <= b]
    res["perp_age_at_listing"][k] = st(x["net"] for x in sub)
res["perp_age_at_listing"]["entry_before_perp_first_bar"] = sum(x["e"] < x["perp_first"] for x in oos)
# entry-day perp liquidity
qv = sorted(perp[x["sym"]][x["e"]][3] for x in oos)
res["entry_day_perp_quote_vol_usd"] = {"min": round(qv[0]), "p10": round(qv[len(qv) // 10]), "median": round(qv[len(qv) // 2])}

# ---- 6. funding ----
fs = sorted(x["fund"] for x in oos)
res["funding"] = {
    "oos_mean_funding_contrib_pct": round(sum(fs) / len(fs) * 100, 3), "min_pct": round(fs[0] * 100, 2), "max_pct": round(fs[-1] * 100, 2),
    "events_without_settlements_in_window": [x["ticker"] for x in oos if not any(
        datetime(x["e"].year, x["e"].month, x["e"].day, tzinfo=timezone.utc) < t <= datetime(x["e"].year, x["e"].month, x["e"].day, tzinfo=timezone.utc) + timedelta(HOLD)
        for t, _ in fund.get(x["sym"], []))],
    "oos_no_funding_x2": st(x["net"] - x["fund"] for x in oos),
    "multiplier_symbols": [{"ticker": x["ticker"], "sym": x["sym"], "net_pct": round(x["net"] * 100, 2), "fund_pct": round(x["fund"] * 100, 3)}
                           for x in oos if x["sym"][0].isdigit()],
}
# ticker collision: Upbit KRW open / usdkrw vs perp open (multiplier-adjusted)
fx = {}
last = None
for r in rows("usdkrw"):
    fx[d(r["date"])] = float(r["usdkrw"])
fxd = {}
dd = date(2019, 12, 1)
while dd <= END:
    last = fx.get(dd, last)
    fxd[dd] = last
    dd += timedelta(1)
need = {f"KRW-{x['ticker']}" for x in oos}
upb = {(r["market"], d(r["date_utc"])): float(r["open"]) for r in rows("upbit_krw_1d") if r["market"] in need}
ratios = []
for x in oos:
    u = upb.get((f"KRW-{x['ticker']}", x["e"]))
    if u is None:
        continue
    mult = 1.0
    for pre, m in (("1000000", 1e6), ("1000", 1e3), ("1M", 1e6)):
        if x["sym"].startswith(pre):
            mult = m
            break
    ratios.append((round(u / fxd[x["e"]] / (perp[x["sym"]][x["e"]][0] / mult), 3), x["ticker"], x["sym"]))
ratios.sort()
res["ticker_collision_check"] = {"n": len(ratios), "ratio_min": ratios[0], "ratio_max": ratios[-1],
                                 "outside_0.8_1.4": [r for r in ratios if not 0.8 <= r[0] <= 1.4]}

# ---- parsing omissions / survivorship ----
pm = list(rows("listing_perp_map"))
res["parsing"] = {
    "first_only_after_2022_01_11": [r["ticker"] for r in pm if r["source"] == "first" and r["upbit_first_date_utc"] >= "2022-01-12"],
    "notice_only_total": [r["ticker"] for r in pm if r["source"] == "notice"],
}

# ---- 5. concentration ----
by_year = defaultdict(list)
for x in events:
    by_year[x["D"].year].append(x["net"])
res["by_year_x2"] = {y: st(v) for y, v in sorted(by_year.items())}
srt = sorted(oos, key=lambda x: x["net"])
res["top5_removed_oos"] = st(x["net"] for x in srt[:-5])
res["top10_removed_oos"] = st(x["net"] for x in srt[:-10])
res["share_2025_26_oos"] = round(sum(x["D"].year >= 2025 for x in oos) / len(oos), 3)
res["oos_2023_24_only"] = st(x["net"] for x in oos if x["D"].year <= 2024)
by_week = defaultdict(list)
for x in oos:
    by_week[x["e"].isocalendar()[:2]].append(x["net"])
wk = [sum(v) / len(v) for v in by_week.values()]
res["oos_week_clustered"] = st(wk)
m = sum(wk) / len(wk)
sd = (sum((w - m) ** 2 for w in wk) / (len(wk) - 1)) ** 0.5
res["oos_week_clustered"]["t_stat"] = round(m / (sd / len(wk) ** 0.5), 2)
by_month = defaultdict(list)
for x in oos:
    by_month[x["e"].strftime("%Y-%m")].append(x["net"])
res["oos_month_means_pct"] = {k: round(sum(v) / len(v) * 100, 1) for k, v in sorted(by_month.items())}

# ---- 4. beta: alt-index short over identical windows (Binance spot, survivorship-free universe) ----
spot = load_bars("binance_spot_usdt_1d")
spot_dates = {s: sorted(b) for s, b in spot.items()}


def base(sym):
    return sym[:-4] if sym.endswith("USDT") else sym


def lev(sym):
    b = base(sym)
    return b.endswith(("UP", "DOWN", "BULL", "BEAR")) and len(b) > 4


def universe(e, n):
    cands = []
    for s, b in spot.items():
        if base(s) in STABLE or lev(s) or e not in b:
            continue
        hist = [b.get(e - timedelta(k)) for k in range(1, 31)]
        if any(h is None for h in hist):
            continue
        cands.append((sum(h[3] for h in hist), s))
    cands.sort(reverse=True)
    return [s for _, s in cands[:n]]


def spot_short(s, e):
    b = spot[s]
    if e not in b:
        return None
    x = e + timedelta(HOLD)
    if x in b:
        p1 = b[x][0]
    else:  # delisted inside window: last close before exit
        prev = [k for k in spot_dates[s] if k < x]
        p1 = b[prev[-1]][2]
    return max(-1.0, -(p1 / b[e][0] - 1))


idx_cache, top100 = {}, {}
for x in oos:
    e = x["e"]
    if e not in idx_cache:
        top100[e] = universe(e, 100)
        t30 = top100[e][:30]
        v = [r for r in (spot_short(s, e) for s in t30) if r is not None]
        idx_cache[e] = sum(v) / len(v) - COST
    x["idx_short"] = idx_cache[e]
ex = [x["net"] - x["idx_short"] for x in oos]
res["beta"] = {
    "oos_alt_index_short_top30_x2": st(x["idx_short"] for x in oos),
    "oos_excess_vs_index_short": st(ex),
    "oos_excess_vs_btc_short_mean_pct": round(sum(x["net"] - x["btc_short"] for x in oos) / len(oos) * 100, 2),
    "excess_by_year": {y: st(x["net"] - x["idx_short"] for x in oos if x["D"].year == y) for y in sorted({x["D"].year for x in oos})},
}
R = random.Random(SEED)
dist = []
for _ in range(1000):
    vals = []
    for x in oos:
        pool = [s for s in top100[x["e"]] if base(s) != x["ticker"]]
        r = None
        while r is None:
            r = spot_short(R.choice(pool), x["e"])
        vals.append(r - COST)
    dist.append(sum(vals) / len(vals))
ds = sorted(dist)
res["beta"]["random_top100_alt_short_same_windows"] = {"pct_rank_of_event_mean": pct_rank(sum(x["net"] for x in oos) / len(oos), dist),
                                                         "random_mean_pct": round(sum(dist) / len(dist) * 100, 2), "random_p95_pct": round(ds[949] * 100, 2)}
# newly-listed control: Binance spot alts whose first bar is within 60 days before e (new-token decay control), not the event coin
newc = []
for x in oos:
    pool = [s for s, ds_ in spot_dates.items() if base(s) not in STABLE and not lev(s) and base(s) != x["ticker"]
            and 0 <= (x["e"] - ds_[0]).days <= 60 and x["e"] in spot[s]]
    v = [r for r in (spot_short(s, x["e"]) for s in pool) if r is not None]
    if v:
        newc.append((x, sum(v) / len(v) - COST))
res["beta"]["new_listing_control_short"] = st(c for _, c in newc)
res["beta"]["excess_vs_new_listing_control"] = st(x["net"] - c for x, c in newc)


# ---- 3. sizing / ruin ----
def simulate(evs, L, stop=None):
    by_entry = defaultdict(list)
    for x in evs:
        by_entry[x["e"]].append(x)
    if not evs:
        return {}
    day, last_day = min(by_entry), max(x["e"] for x in evs) + timedelta(HOLD)
    cash, pos, curve, maxgross, liq, stops, ruin = 1.0, [], [], 0.0, 0, 0, None
    while day <= last_day:
        t0 = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        # exits at open
        keep = []
        for p in pos:
            if p["x"] == day:
                px = perp[p["sym"]][day][0]
                cash += p["q"] * (p["p0"] - px) - p["q"] * px * COST / 2
            else:
                keep.append(p)
        pos = keep
        # equity at open (mark to open)
        eq_open = cash + sum(p["q"] * (p["p0"] - perp[p["sym"]].get(day, (p["p0"],))[0]) for p in pos)
        new = by_entry.get(day, [])
        if new and eq_open > 0:
            margin = eq_open / (len(pos) + len(new))
            for x in new:
                p0 = perp[x["sym"]][day][0]
                q = L * margin / p0
                cash -= q * p0 * COST / 2
                pos.append({"sym": x["sym"], "p0": p0, "q": q, "m": margin, "x": day + timedelta(HOLD)})
        # intraday stop / liquidation via daily high
        keep = []
        for p in pos:
            o, h, c, _ = perp[p["sym"]][day]
            if stop and h >= p["p0"] * (1 + stop):
                px = max(o, p["p0"] * (1 + stop))
                cash += p["q"] * (p["p0"] - px) - p["q"] * px * COST / 2
                stops += 1
                continue
            if h >= p["p0"] * (1 + 1 / L - MM):
                cash -= p["m"]
                liq += 1
                continue
            keep.append(p)
        pos = keep
        # funding settlements in (day, day+1]
        for p in pos:
            o = perp[p["sym"]][day][0]
            for t, r in fund.get(p["sym"], []):
                if t0 < t <= t0 + timedelta(1):
                    cash += p["q"] * o * r
        eq = cash + sum(p["q"] * (p["p0"] - perp[p["sym"]][day][2]) for p in pos)
        if eq > 0 and pos:
            maxgross = max(maxgross, sum(p["q"] * perp[p["sym"]][day][2] for p in pos) / eq)
        curve.append((day, eq))
        if eq <= 0:
            ruin = str(day)
            break
        day += timedelta(1)
    peak, mdd = curve[0][1], 0.0
    for _, v in curve:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    months, prev = {}, 1.0
    for k, v in curve:
        months[k.strftime("%Y-%m")] = v
    mret = {}
    for k in sorted(months):
        mret[k] = months[k] / prev - 1
        prev = months[k]
    worst = min(mret.items(), key=lambda kv: kv[1])
    yearly, prev = {}, 1.0
    for k in sorted(months):
        yearly[k[:4]] = months[k]
    yret = {}
    for y in sorted(yearly):
        yret[y] = round((yearly[y] / prev - 1) * 100, 1)
        prev = yearly[y]
    return {"final_equity": round(curve[-1][1], 3), "mdd_pct": round(mdd * 100, 1), "worst_month": (worst[0], round(worst[1] * 100, 1)),
            "liquidations": liq, "stops": stops, "ruin_date": ruin, "max_gross_x_equity": round(maxgross, 2), "by_year_pct": yret}


res["sizing_oos"] = {f"L{L}": simulate(oos, L) for L in (1, 2, 3)}
res["sizing_oos"]["L1_stop30_NOT_FROZEN"] = simulate(oos, 1, stop=0.30)
res["sizing_oos"]["L2_stop30_NOT_FROZEN"] = simulate(oos, 2, stop=0.30)
res["sizing_full"] = {f"L{L}": simulate(events, L) for L in (1, 2, 3)}
# worst intraday adverse excursion (max high in hold / entry - 1)
mae = sorted(max(perp[x["sym"]][x["e"] + timedelta(k)][1] for k in range(HOLD)) / perp[x["sym"]][x["e"]][0] - 1 for x in oos)
res["oos_max_adverse_excursion"] = {"p50_pct": round(mae[len(mae) // 2] * 100, 1), "p90_pct": round(mae[int(len(mae) * 0.9)] * 100, 1),
                                    "max_pct": round(mae[-1] * 100, 1), "n_ge_32pct(L3 liq)": sum(m >= 1 / 3 - MM for m in mae),
                                    "n_ge_49pct(L2 liq)": sum(m >= 0.5 - MM for m in mae), "n_ge_30pct": sum(m >= 0.30 for m in mae)}
# ---- clean set: drop dead perps (zero-volume flat bars at entry) and ambiguous listing dates ----
dead = {x["ticker"] for x in oos if perp[x["sym"]][x["e"]][3] == 0}
ambiguous = {"BIGTIME", "IO"}  # notice 135 / 386 days before first KRW candle
clean = [x for x in oos if x["ticker"] not in dead | ambiguous]
res["clean"] = {"dropped_dead_perp": sorted(dead), "dropped_ambiguous_date": sorted(ambiguous), "oos_x2": st(x["net"] for x in clean),
                "sizing_L1": simulate(clean, 1)}

# ---- perp listed AFTER Upbit listing (excluded by card), treated separately ----
late = []
for r in rows("listing_perp_map"):
    D = d(r["upbit_first_date_utc"]) if r["upbit_first_date_utc"] else d(r["notice_kst"])
    sym = r["perp_symbol"]
    if not (OOS0 <= D <= END - timedelta(1 + HOLD)) or not sym or sym not in perp or min(perp[sym]) < D:
        continue
    e = max(D + timedelta(1), min(perp[sym]) + timedelta(1))
    g = short_ret(sym, e)
    if g is not None:
        late.append({"lag_days": (min(perp[sym]) - D).days, "net": g - COST})
res["perp_after_listing_oos"] = {"all": st(x["net"] for x in late), "perp_within_7d": st(x["net"] for x in late if x["lag_days"] <= 7),
                                 "perp_after_7d": st(x["net"] for x in late if x["lag_days"] > 7)}

res["oos_events"] = [{"t": x["ticker"], "D": str(x["D"]), "sym": x["sym"], "age": (x["D"] - x["perp_first"]).days,
                      "net": round(x["net"] * 100, 1), "idx": round(x["idx_short"] * 100, 1)} for x in oos]

OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
for k, v in res.items():
    if k != "oos_events":
        print(k, json.dumps(v, ensure_ascii=False, default=str))
