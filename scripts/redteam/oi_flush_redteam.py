#!/usr/bin/env python3
"""T-032 red-team for oi-flush-rebound (perp / Bitget-proxy). Reuses scripts/bt_oi_flush_rebound.py unchanged.

Run: python scripts/redteam/oi_flush_redteam.py  -> scripts/redteam/oi_flush_redteam_out.json
"""
from __future__ import annotations

import json
import math
import random
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import bt_oi_flush_rebound as B  # noqa: E402
from bt_cards_common import N_RANDOM, SEED, daily_bars, pct_rank, summarize  # noqa: E402

DAY, OOS0, END, COINS = B.DAY, B.OOS0, B.END, B.COINS


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def load():
    perp_raw = daily_bars("binance_perp_1d", only={f"{c}USDT" for c in COINS})
    perp = {c: perp_raw[f"{c}USDT"] for c in COINS}
    up_raw = daily_bars("upbit_krw_1d", key="market", only={f"KRW-{c}" for c in COINS})
    upbit = {c: up_raw[f"KRW-{c}"] for c in COINS}
    fund = {c: B.funding_by_day(f"{c}USDT") for c in COINS}
    pret = {c: {D: v[1] / v[0] - 1 for D, v in perp[c].items()} for c in COINS}
    return perp, upbit, fund, pret


def oos(tr):
    return [t for t in tr if t["date"] >= OOS0]


def st(tr, k="x2"):
    s = summarize([t[k] for t in tr])
    return {k2: s.get(k2) for k2 in ("n", "mean_pct", "pf", "win_pct")}


def load_doi_stale_only(col="oi"):
    """Addendum literal: drop stale day S and S+1 only (not S-1)."""
    oi, stale = {}, {}
    for r in B.rows("binance_oi_1d"):
        c = r["symbol"].replace("USDT", "")
        D = B.d(r["date_utc"])
        if c not in COINS or D < B.START:
            continue
        oi.setdefault(c, {})[D] = float(r[col])
        if int(r["stale_min"]) > 60:
            stale.setdefault(c, set()).add(D)
    out = {}
    for c, s in oi.items():
        bad = set()
        for S in stale.get(c, ()):
            bad |= {S, S + DAY}
        out[c] = {D: s[D + DAY] / s[D] - 1 for D in s if D + DAY in s and D not in bad}
    return out


def null_independent(oos_tr, bars, fund, seed, cost_slip=None):
    """Researcher's null (coins independent), arbitrary seed."""
    R = random.Random(seed)
    pre = {c: [D for D in sorted(bars[c]) if OOS0 <= D <= END and D + 3 * DAY in bars[c]] for c in COINS}
    by = {c: sum(t["sym"] == c for t in oos_tr) for c in COINS}
    out = []
    for _ in range(N_RANDOM):
        rs = []
        for c in COINS:
            sl = B.SLIP[c] if cost_slip is None else cost_slip[c]
            rs += [B.trade_ret(R.choice(pre[c]) + DAY, bars[c], B.FEE["perp"]["x2"], sl, fund[c]) for _ in range(by[c])]
        out.append(mean(rs))
    return out


def null_clustered(oos_tr, bars, fund, seed):
    """Keeps the cross-coin clustering: each signal date (with its coin set) moves to one random date together."""
    R = random.Random(seed)
    common = [D for D in sorted(bars["BTC"]) if OOS0 <= D <= END and all(D + 3 * DAY in bars[c] for c in COINS)]
    groups: dict = {}
    for t in oos_tr:
        groups.setdefault(t["date"], []).append(t["sym"])
    out = []
    for _ in range(N_RANDOM):
        rs = []
        for coins in groups.values():
            D = R.choice(common)
            rs += [B.trade_ret(D + DAY, bars[c], B.FEE["perp"]["x2"], B.SLIP[c], fund[c]) for c in coins]
        out.append(mean(rs))
    return out


def null_down_days(oos_tr, bars, fund, pret, seed):
    """Same coin, same count, random OOS days where the perp closed down (any size). Is OI better than 'bought a red day'?"""
    R = random.Random(seed)
    pre = {c: [D for D in sorted(bars[c]) if OOS0 <= D <= END and D + 3 * DAY in bars[c] and pret[c].get(D, 0) < 0]
           for c in COINS}
    by = {c: sum(t["sym"] == c for t in oos_tr) for c in COINS}
    out = []
    for _ in range(N_RANDOM):
        rs = []
        for c in COINS:
            rs += [B.trade_ret(R.choice(pre[c]) + DAY, bars[c], B.FEE["perp"]["x2"], B.SLIP[c], fund[c]) for _ in range(by[c])]
        out.append(mean(rs))
    return out


def rolling_pf(tr, w=20):
    out = []
    for i in range(w, len(tr) + 1):
        rs = [t["x2"] for t in tr[i - w:i]]
        g, l = sum(x for x in rs if x > 0), -sum(x for x in rs if x < 0)
        out.append({"end": str(tr[i - 1]["date"]), "pf": round(g / l, 2) if l else None, "mean_pct": round(mean(rs) * 100, 2)})
    return out


def main():
    perp, upbit, fund, pret = load()
    doi, _ = B.load_doi("oi")
    sig, ctrl_sig, th = B.signals(doi, pret)
    trades = B.run(sig, "perp", perp, fund)
    o = oos(trades)
    res: dict = {}

    # 0. reproduce
    ref = json.loads((ROOT / "reports/research-cards/oi-flush-rebound.json").read_text(encoding="utf-8"))["perp"]
    rd = B.random_dist({c: [t for t in o if t["sym"] == c] for c in COINS}, perp, "perp", fund)
    res["reproduce"] = {"ours": {**st(o), "rand_pct": pct_rank(mean([t["x2"] for t in o]), rd)},
                        "ref": {"n": ref["oos_x2"]["n"], "mean_pct": ref["oos_x2"]["mean_pct"], "pf": ref["oos_x2"]["pf"],
                                "rand_pct": ref["random_oos_x2"]["pct_rank"]}}
    om = mean([t["x2"] for t in o])

    # 1. random null: seed sensitivity, clustered null, down-day null
    seeds = [SEED + i for i in range(20)]
    ind = [pct_rank(om, null_independent(o, perp, fund, s)) for s in seeds]
    clu = [pct_rank(om, null_clustered(o, perp, fund, s)) for s in seeds]
    dwn = [pct_rank(om, null_down_days(o, perp, fund, pret, s)) for s in seeds[:5]]
    res["random"] = {
        "independent_20_seeds": {"min": min(ind), "median": sorted(ind)[10], "max": max(ind), "share_ge95": sum(x >= 95 for x in ind) / 20},
        "clustered_20_seeds": {"min": min(clu), "median": sorted(clu)[10], "max": max(clu), "share_ge95": sum(x >= 95 for x in clu) / 20},
        "down_day_5_seeds": dwn,
        "unique_signal_dates_oos": len({t["date"] for t in o}),
    }
    # date-clustered t-stat (cluster = signal date)
    g: dict = {}
    for t in o:
        g.setdefault(t["date"], []).append(t["x2"])
    cm = [mean(v) for v in g.values()]
    m, sd = mean(cm), math.sqrt(sum((x - mean(cm)) ** 2 for x in cm) / (len(cm) - 1))
    tr_ = [t["x2"] for t in o]
    sdt = math.sqrt(sum((x - om) ** 2 for x in tr_) / (len(tr_) - 1))
    res["t_stat"] = {"naive_trade_t": round(om / sdt * math.sqrt(len(tr_)), 2),
                     "date_cluster_t": round(m / sd * math.sqrt(len(cm)), 2), "n_clusters": len(cm)}

    # 2. lookahead / timing variants
    doi_pre, _ = B.load_doi("oi_pre")
    sp, _, _ = B.signals(doi_pre, pret)
    tp = oos(B.run(sp, "perp", perp, fund))
    doi_s = load_doi_stale_only("oi")
    ss, _, ths = B.signals(doi_s, pret)
    ts = B.run(ss, "perp", perp, fund)
    res["timing"] = {
        "oi_pre_2355_perp_oos": {**st(tp), "rand_pct_ind": pct_rank(mean([t["x2"] for t in tp]), null_independent(tp, perp, fund, SEED)),
                                 "rand_pct_clu": pct_rank(mean([t["x2"] for t in tp]), null_clustered(tp, perp, fund, SEED))},
        "stale_drop_S_S1_only": {"thresholds": ths, "oos": st(oos(ts)),
                                 "trade_diff": sorted({(str(t["date"]), t["sym"]) for t in ts} ^ {(str(t["date"]), t["sym"]) for t in trades})},
        "thresholds_train_only": th,
    }
    # entry one day later (D+2 open): does the edge depend on catching the exact 00:00 open?
    def run_lag(lag):
        out = []
        for c in COINS:
            free = date.min
            for D in sig[c]:
                E = D + lag * DAY
                if E < free:
                    continue
                r = B.trade_ret(E, perp[c], B.FEE["perp"]["x2"], B.SLIP[c], fund[c])
                if r is None:
                    continue
                out.append({"sym": c, "date": D, "x2": r})
                free = E + 2 * DAY
        return sorted(out, key=lambda t: (t["date"], t["sym"]))
    res["timing"]["entry_D+2_open_oos"] = st(oos(run_lag(2)))

    # 3. concentration
    srt = sorted(o, key=lambda t: t["x2"], reverse=True)
    res["concentration"] = {
        "top_trades": [{"date": str(t["date"]), "sym": t["sym"], "x2_pct": round(t["x2"] * 100, 2)} for t in srt[:6]],
        "drop_top3": st(srt[3:]), "drop_top5": st(srt[5:]),
        "ex_SOL": st([t for t in o if t["sym"] != "SOL"]),
        "SOL_oos_trades": [{"date": str(t["date"]), "x2_pct": round(t["x2"] * 100, 2)} for t in o if t["sym"] == "SOL"],
        "per_coin": {c: st([t for t in o if t["sym"] == c]) for c in COINS},
        "leave_one_date_out_min_mean_pct": round(min(mean([t["x2"] for t in o if t["date"] != D]) for D in g) * 100, 3),
        "drop_top3_dates": st([t for t in o if t["date"] not in sorted(g, key=lambda D: -sum(g[D]))[:3]]),
        "ex_SOL_rand_pct_ind": pct_rank(mean([t["x2"] for t in o if t["sym"] != "SOL"]),
                                        null_independent([t for t in o if t["sym"] != "SOL"], perp, fund, SEED)),
    }

    # 4. regime decay
    years: dict = {}
    for t in o:
        years.setdefault(t["date"].year, []).append(t)
    res["regime"] = {"oos_by_year": {y: st(v) for y, v in sorted(years.items())},
                     "since_2025": st([t for t in o if t["date"] >= date(2025, 1, 1)]),
                     "rolling20_pf": rolling_pf(o)[::5] + rolling_pf(o)[-1:]}

    # 5. execution stress (slippage per side, crash-day open)
    def with_slip(sl):
        return [B.trade_ret(t["date"] + DAY, perp[t["sym"]], B.FEE["perp"]["x2"], sl[t["sym"]], fund[t["sym"]]) for t in o]
    res["exec"] = {}
    for name, sl in {"slip_10_10_20bps": {"BTC": .001, "ETH": .001, "SOL": .002},
                     "slip_20_20_40bps": {"BTC": .002, "ETH": .002, "SOL": .004}}.items():
        rs = with_slip(sl)
        rp = pct_rank(mean(rs), null_independent(o, perp, fund, SEED, cost_slip=sl))
        res["exec"][name] = {"mean_pct": round(mean(rs) * 100, 3), "pf": summarize(rs)["pf"], "rand_pct_same_cost": rp}
    fsum = [sum(fund[t["sym"]].get(t["date"] + DAY + i * DAY, 0.0) for i in range(2)) for t in o]
    res["exec"]["funding_paid_mean_pct"] = round(mean(fsum) * 100, 4)
    res["exec"]["entry_quote_volume_musd_min_SOL"] = round(min(perp["SOL"][t["date"] + DAY][2] for t in o if t["sym"] == "SOL") / 1e6, 1)
    # Upbit vs perp gross path gap on the same trades (venue sensitivity)
    gaps = [(perp[t["sym"]][t["date"] + 3 * DAY][0] / perp[t["sym"]][t["date"] + DAY][0])
            - (upbit[t["sym"]][t["date"] + 3 * DAY][0] / upbit[t["sym"]][t["date"] + DAY][0]) for t in o
            if t["date"] + 3 * DAY in upbit[t["sym"]] and t["date"] + DAY in upbit[t["sym"]]]
    res["exec"]["perp_minus_upbit_gross_pp"] = {"mean": round(mean(gaps) * 100, 3), "n": len(gaps),
                                                "share_positive": round(sum(x > 0 for x in gaps) / len(gaps), 2)}

    p = Path(__file__).with_name("oi_flush_redteam_out.json")
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
