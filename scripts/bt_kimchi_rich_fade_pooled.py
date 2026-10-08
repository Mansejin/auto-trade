#!/usr/bin/env python3
"""Card kimchi-rich-fade-pooled (frozen 2026-10-08), encoded as-is.

Premium(D) = Upbit close(D) / (Binance close(D) * USDKRW(D, ffill past only)) - 1.  Both closes = D+1 00:00 UTC;
ECB fix for D is published ~13:15 UTC D, so it is known at decision time.
Signal: premium(D) >= 90th pct of the previous 365 daily premiums (D excluded, need 365 values).
Event: skip Upbit buys D+1..D+3 -> event return = Upbit open(D+4)/open(D+1) - 1. Same-symbol signals within 3 days -> 1 event.
Baseline = mean of all 3-day open-to-open returns of the same symbol/period.
Skip value (card PF) = -(event_ret - 20bps): avoided loss minus missed gain with round-trip fee x2.
Days with Binance USDCUSDT close outside [0.98, 1.02] are dropped (USDT depeg flag).
"""
from __future__ import annotations

from datetime import date, timedelta

from bt_cards_common import N_RANDOM, d, daily_bars, halves, pct_rank, pf, rng, rows, summarize, write_json

SLUG = "kimchi-rich-fade-pooled"
Q, WIN, H = 0.90, 365, 3
FEE_X2 = 0.002
TRAIN0, OOS0, END = date(2019, 1, 1), date(2023, 1, 1), date(2026, 9, 30)
PAIRS = {"BTC": ("KRW-BTC", "BTCUSDT"), "ETH": ("KRW-ETH", "ETHUSDT"), "XRP": ("KRW-XRP", "XRPUSDT")}


def quantile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    k = q * (len(s) - 1)
    lo = int(k)
    return s[lo] + (s[min(lo + 1, len(s) - 1)] - s[lo]) * (k - lo)


def main():
    up = daily_bars("upbit_krw_1d", key="market", only={m for m, _ in PAIRS.values()})
    bn = daily_bars("binance_spot_1d")
    usdc = daily_bars("binance_spot_usdt_1d", only={"USDCUSDT"}).get("USDCUSDT", {})
    fx_raw = {d(r["date"]): float(r["usdkrw"]) for r in rows("usdkrw")}
    fx, last = {}, None
    for D in sorted({x for v in up.values() for x in v}):
        last = fx_raw.get(D, last)  # forward-fill only from past fixes
        if last is not None:
            fx[D] = last
    depeg = {D for D, b in usdc.items() if not 0.98 <= b[1] <= 1.02}

    events, base, res = [], {}, {"per_symbol": {}}
    for s, (um, bm) in PAIRS.items():
        u, b = up[um], bn[bm]
        days = sorted(D for D in u if D in b and D in fx and D not in depeg)
        prem = [(D, u[D][1] / (b[D][1] * fx[D]) - 1) for D in days]
        fwd = lambda D: u[D + timedelta(1 + H)][0] / u[D + timedelta(1)][0] - 1 if D + timedelta(1) in u and D + timedelta(1 + H) in u else None  # noqa: E731
        free = date.min
        for i in range(WIN, len(prem)):
            D, p = prem[i]
            if not (TRAIN0 <= D <= END) or D < free:
                continue
            if p >= quantile([x for _, x in prem[i - WIN:i]], Q):
                r = fwd(D)
                if r is not None:
                    events.append({"sym": s, "date": D, "prem": round(p, 4), "ret": r})
                    free = D + timedelta(H)
        base[s] = {D: fwd(D) for D in u if TRAIN0 <= D <= END and fwd(D) is not None}

    def block(evs, a, b):
        out = {}
        for s in list(PAIRS) + ["pooled"]:
            ev = [e for e in evs if a <= e["date"] < b and (s == "pooled" or e["sym"] == s)]
            syms = list(PAIRS) if s == "pooled" else [s]
            bl = [r for x in syms for D, r in base[x].items() if a <= D < b]
            if not ev:
                out[s] = {"n": 0}
                continue
            m = sum(e["ret"] for e in ev) / len(ev)
            bm = sum(bl) / len(bl)
            skip = [-(e["ret"] - FEE_X2) for e in ev]
            out[s] = {"n": len(ev), "event_mean_pct": round(m * 100, 3), "baseline_mean_pct": round(bm * 100, 3),
                      "fade_edge_pct": round((bm - m) * 100, 3), "skip_pf_x2": pf(skip), "skip_summary_x2": summarize(skip),
                      "event_win_pct": round(sum(e["ret"] > 0 for e in ev) / len(ev) * 100, 1)}
        return out

    oos_ev = [e for e in events if e["date"] >= OOS0]
    h1, h2 = halves(oos_ev, lambda e: e["date"])
    mid = h2[0]["date"] if h2 else END
    res["full"] = block(events, TRAIN0, END + timedelta(1))
    res["train"] = block(events, TRAIN0, OOS0)
    res["oos"] = block(events, OOS0, END + timedelta(1))
    res["oos_h1"] = block(events, OOS0, mid)
    res["oos_h2"] = block(events, mid, END + timedelta(1))

    # random: same number of OOS events per symbol on random dates; fade wants a LOW mean -> rank -mean
    R = rng()
    pools = {s: [r for D, r in base[s].items() if D >= OOS0] for s in PAIRS}
    ns = {s: sum(e["sym"] == s for e in oos_ev) for s in PAIRS}
    dist = []
    for _ in range(N_RANDOM):
        xs = [r for s in PAIRS for r in R.sample(pools[s], ns[s])]
        dist.append(-sum(xs) / len(xs))
    actual = -sum(e["ret"] for e in oos_ev) / len(oos_ev) if oos_ev else 0.0
    res["oos_random_pct"] = pct_rank(actual, dist)
    res["oos_bh_3d_mean_pct"] = res["oos"]["pooled"].get("baseline_mean_pct")
    res["events"] = [{**e, "date": str(e["date"]), "ret": round(e["ret"], 5)} for e in events]

    o, why = res["oos"]["pooled"], []
    n_full = res["full"]["pooled"].get("n", 0)
    if o.get("n", 0) == 0 or o["fade_edge_pct"] <= 0:
        why.append(f"OOS fade edge {o.get('fade_edge_pct')} <= 0")
    if (o.get("skip_pf_x2") or 0) < 1.1:
        why.append(f"OOS skip PF x2 {o.get('skip_pf_x2')} < 1.1")
    if res["oos_random_pct"] < 95:
        why.append(f"random pct {res['oos_random_pct']} < 95")
    wrong = [s for s in PAIRS if (res["oos"][s].get("fade_edge_pct") or 0) <= 0]
    if len(wrong) >= 2:
        why.append(f"symbol sign: {wrong} opposite")
    res["verdict"] = "INCONCLUSIVE" if n_full < 30 else ("KILL" if why else "SURVIVE")
    res["reasons"] = why
    path = write_json(SLUG, res)
    for k in ("full", "train", "oos", "oos_h1", "oos_h2"):
        print(k, res[k])
    print(res["oos_random_pct"], res["verdict"], why, path)


if __name__ == "__main__":
    main()
