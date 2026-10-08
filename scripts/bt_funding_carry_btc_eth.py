#!/usr/bin/env python3
"""Card funding-carry-btc-eth (frozen 2026-10-08), encoded as-is.

Decision after the last settlement of UTC day D (<= D 23:59): mean of last 21 Binance settlements.
Flat and mean >= +0.01%  -> at D+1 00:00 open buy spot + short perp (1x, same notional N).
Long  and mean <  0      -> at D+1 00:00 open close both.
Capital per sleeve = 2N (spot N + 1x perp margin N); also reported per notional N.
Funding received for settlements t with entry < t <= exit (position held at the settlement).
BTC and ETH sleeves independent, portfolio 50:50 (no rebalance). Idle cash earns 0.
Costs per cycle on N: spot 0.1%x2 + perp 0.05%x2 (base); x2 stress doubles each.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from bt_cards_common import N_RANDOM, d, pct_rank, rng, rows, summarize, write_json

SLUG = "funding-carry-btc-eth"
WIN, ENTER, EXIT = 21, 0.0001, 0.0
FEE = {"base": (0.001, 0.0005), "x2": (0.002, 0.001)}
OOS0, END = date(2023, 1, 1), date(2026, 9, 30)


def load(sym: str):
    fund = sorted((datetime.fromisoformat(r["funding_time_utc"].replace("Z", "+00:00")), float(r["funding_rate"]))
                  for r in rows("funding") if r["exchange"] == "binance" and r["symbol"] == sym)
    spot = {d(r["date_utc"]): (float(r["open"]), float(r["close"])) for r in rows("binance_spot_1d") if r["symbol"] == sym}
    perp = {d(r["date_utc"]): (float(r["open"]), float(r["close"])) for r in rows("binance_perp_1d") if r["symbol"] == sym}
    return fund, spot, perp


def cycles(fund, spot, perp, always_on_from: date | None = None) -> list[tuple[date, date]]:
    """[(entry_day, exit_day)] trading at the 00:00 open of those days."""
    days = sorted(set(spot) & set(perp))
    if always_on_from:
        ds = [x for x in days if x >= always_on_from]
        return [(ds[0], ds[-1])]
    out, i, held, entry = [], 0, False, None
    for D in days[:-1]:
        cutoff = datetime(D.year, D.month, D.day, tzinfo=timezone.utc) + timedelta(days=1)
        while i < len(fund) and fund[i][0] < cutoff:
            i += 1
        if i < WIN:
            continue
        m = sum(r for _, r in fund[i - WIN:i]) / WIN
        nxt = D + timedelta(1)
        if not held and m >= ENTER:
            held, entry = True, nxt
        elif held and m < EXIT:
            out.append((entry, nxt))
            held = False
    if held:
        out.append((entry, days[-1]))
    return out


def sleeve(fund, spot, perp, cyc, fee: tuple, start: date, end: date) -> dict:
    """Daily (open-to-open) equity on capital 2N, plus per-cycle return on N."""
    fs, ff = fee
    days = [x for x in sorted(set(spot) & set(perp)) if start <= x <= end]
    fund_by_day: dict = {}
    for t, r in fund:
        # settlement at t is paid to a position held at t; day bucket = the open-to-open interval (D 00:00, D+1 00:00]
        key = (t - timedelta(microseconds=1)).date() if (t.hour, t.minute, t.second) == (0, 0, 0) else t.date()
        fund_by_day[key] = fund_by_day.get(key, 0.0) + r
    # ponytail: notional re-set to equity/2 every day (no rebalance fee). Fixed-qty 1x shorts get liquidated
    # in 2020-21 (ETH 20x) and inflate funding on drifting notional; daily reset keeps cycle and always-on comparable.
    eq, curve, cyc_rets, worst_days = 1.0, {}, [], []
    held = {}
    for e, x in cyc:
        for D in days:
            if e <= D < x:
                held[D] = (e, x)
    cur = None
    for k, D in enumerate(days[:-1]):
        D1 = days[k + 1]
        h = held.get(D)
        if h:
            if cur is None or cur["e"] != h[0]:
                cur = {"e": h[0], "x": h[1], "g": 1.0}
            r = (spot[D1][0] / spot[D][0] - 1) - (perp[D1][0] / perp[D][0] - 1) + fund_by_day.get(D, 0.0)
            r -= (fs + ff) * ((D == cur["e"]) + (D1 == cur["x"]))
            worst_days.append((spot[D][1] / spot[D][0]) - (perp[D][1] / perp[D][0]))
            eq *= 1 + r / 2
            cur["g"] *= 1 + r
            if D1 == cur["x"]:
                cyc_rets.append((cur["e"], cur["g"] - 1))
                cur = None
        curve[D1] = eq
    return {"curve": curve, "cyc": cyc_rets, "worst_basis_days_lt_-3pct": sum(w < -0.03 for w in worst_days)}


def period(curve: dict, a: date, b: date) -> dict:
    ds = [x for x in sorted(curve) if a <= x <= b]
    e0, e1 = curve[ds[0]], curve[ds[-1]]
    yrs = (ds[-1] - ds[0]).days / 365
    peak, mdd, rets, prev = e0, 0.0, [], e0
    for x in ds:
        peak = max(peak, curve[x])
        mdd = min(mdd, curve[x] / peak - 1)
    return {"ret_pct": round((e1 / e0 - 1) * 100, 2), "ann_pct": round(((e1 / e0) ** (1 / yrs) - 1) * 100, 2), "mdd_pct": round(mdd * 100, 2)}


def portfolio(curves: list[dict]) -> dict:
    common = sorted(set.intersection(*[set(c) for c in curves]))
    return {x: sum(c[x] / c[common[0]] for c in curves) / len(curves) for x in common}


def random_dist(data: dict, cyc_by: dict, fee: tuple) -> list[float]:
    """Same cycle durations as OOS cycles, random start days in OOS; total OOS return (sum of cycle returns on N)."""
    R = rng()
    out = []
    pre = {}
    for s, (fund, spot, perp) in data.items():
        days = [x for x in sorted(set(spot) & set(perp)) if OOS0 <= x <= END]
        durs = [(x - e).days for e, x in cyc_by[s] if e >= OOS0]
        pre[s] = (days, durs)
    for _ in range(N_RANDOM):
        tot = 0.0
        for s, (fund, spot, perp) in data.items():
            days, durs = pre[s]
            cyc = []
            for L in durs:
                L = min(L, len(days) - 2)
                e = days[R.randrange(0, len(days) - L - 1)]
                cyc.append((e, e + timedelta(L)))
            for e, x in cyc:
                r = sleeve(fund, spot, perp, [(e, x)], fee, e, x)["cyc"]
                tot += r[0][1] if r else 0.0
        out.append(tot)
    return out


def main():
    data = {s: load(s) for s in ("BTCUSDT", "ETHUSDT")}
    res: dict = {"sleeves": {}}
    cyc_by = {s: cycles(*v) for s, v in data.items()}
    curves = {k: [] for k in ("base", "x2", "always_x2")}
    for s, (fund, spot, perp) in data.items():
        st = min(set(spot) & set(perp))
        sl = {}
        for fk in ("base", "x2"):
            sl[fk] = sleeve(fund, spot, perp, cyc_by[s], FEE[fk], st, END)
            curves[fk].append(sl[fk]["curve"])
        aon = sleeve(fund, spot, perp, cycles(fund, spot, perp, always_on_from=OOS0), FEE["x2"], OOS0, END)
        curves["always_x2"].append(aon["curve"])
        oos_c = [r for e, r in sl["x2"]["cyc"] if e >= OOS0]
        res["sleeves"][s] = {
            "cycles_total": len(cyc_by[s]), "cycles_oos": len(oos_c),
            "cycles_x2_full": summarize([r for _, r in sl["x2"]["cyc"]]),
            "cycles_x2_oos": summarize(oos_c),
            "cycles_base_oos": summarize([r for e, r in sl["base"]["cyc"] if e >= OOS0]),
            "oos_x2_curve": period(sl["x2"]["curve"], OOS0, END),
            "always_on_oos_x2": period(aon["curve"], OOS0, END),
            "worst_basis_days_lt_-3pct": sl["x2"]["worst_basis_days_lt_-3pct"],
            "cycles": [(str(e), str(x)) for e, x in cyc_by[s]],
        }
    pf_all = {fk: portfolio(curves[fk]) for fk in curves}
    st = min(pf_all["base"])
    oos_days = sorted(x for x in pf_all["x2"] if x >= OOS0)
    mid = oos_days[len(oos_days) // 2]
    res["portfolio"] = {
        "full_base": period(pf_all["base"], st, END), "full_x2": period(pf_all["x2"], st, END),
        "train_base": period(pf_all["base"], st, OOS0), "oos_base": period(pf_all["base"], OOS0, END),
        "oos_x2": period(pf_all["x2"], OOS0, END),
        "oos_h1_x2": period(pf_all["x2"], OOS0, mid), "oos_h2_x2": period(pf_all["x2"], mid, END),
        "always_on_oos_x2": period(pf_all["always_x2"], OOS0, END),
    }
    oos_cyc_x2 = [r for s in data for e, r in sleeve(*data[s], cyc_by[s], FEE["x2"], min(set(data[s][1]) & set(data[s][2])), END)["cyc"] if e >= OOS0]
    res["oos_cycles_x2_pooled"] = summarize(oos_cyc_x2)
    dist = random_dist(data, cyc_by, FEE["x2"])
    res["oos_random_pct_x2"] = pct_rank(sum(oos_cyc_x2), dist)
    res["oos_sum_cycle_ret_on_N_pct"] = round(sum(oos_cyc_x2) * 100, 2)
    res["random_p95_sum_pct"] = round(sorted(dist)[int(0.95 * N_RANDOM)] * 100, 2)
    # per-notional view: capital N (spot as perp collateral) doubles returns ~linearly
    res["oos_x2_ann_on_notional_pct_approx"] = round(res["portfolio"]["oos_x2"]["ann_pct"] * 2, 2)

    p, why = res["portfolio"], []
    n_cyc = sum(len(c) for c in cyc_by.values())
    if p["oos_x2"]["ann_pct"] <= 4.0:  # card: OOS annual net <= 4% -> KILL (x2 is the conservative read)
        why.append(f"OOS ann x2 {p['oos_x2']['ann_pct']}% <= 4% (capital 2N)")
    if p["oos_base"]["ann_pct"] <= 4.0:
        why.append(f"OOS ann base {p['oos_base']['ann_pct']}% <= 4%")
    if p["oos_x2"]["ret_pct"] <= 0 or (res["oos_cycles_x2_pooled"].get("pf") or 0) < 1.1:
        why.append("fee x2: OOS net <= 0 or cycle PF < 1.1")
    a = p["always_on_oos_x2"]
    if p["oos_x2"]["ret_pct"] < a["ret_pct"] or p["oos_x2"]["mdd_pct"] < a["mdd_pct"]:
        why.append(f"vs always-on: ret {p['oos_x2']['ret_pct']} vs {a['ret_pct']}, mdd {p['oos_x2']['mdd_pct']} vs {a['mdd_pct']}")
    if res["oos_random_pct_x2"] < 95:
        why.append(f"random pct {res['oos_random_pct_x2']} < 95")
    res["cycles_total"] = n_cyc
    # cycle-count gate covers trade statistics (PF, random); period-level curve tests (4% hurdle, always-on) still bind
    curve_kill = [w for w in why if w.startswith(("OOS ann x2", "vs always-on"))]
    res["verdict"] = ("KILL" if curve_kill else "INCONCLUSIVE") if n_cyc < 30 else ("KILL" if why else "SURVIVE")
    res["reasons"] = why
    path = write_json(SLUG, res)
    for s, v in res["sleeves"].items():
        print(s, {k: x for k, x in v.items() if k != "cycles"})
    print(res["portfolio"])
    print({k: res[k] for k in ("oos_cycles_x2_pooled", "oos_random_pct_x2", "oos_sum_cycle_ret_on_N_pct", "random_p95_sum_pct", "cycles_total", "verdict", "reasons")}, path)


if __name__ == "__main__":
    main()
