#!/usr/bin/env python3
"""Card xs-alt-momentum-weekly (frozen 2026-10-08), encoded as-is.

Every Monday M 00:00 UTC (point-in-time, data through Sunday M-1 close only):
  universe = top 30 Binance USDT spot pairs by quote volume over M-30..M-1, excluding BTC, stables,
  wrapped/pegged and leveraged tokens; must have closes at M-1 and M-29 and an open at M.
  rank by close(M-1)/close(M-29)-1, hold top 5 equal weight from open(M) to open(M+7).
Delisted (BREAK or no bar) before M+7 -> last close before M+7 * 0.5. Delisted symbols are in the data.
Costs per side on traded weight: base 0.1% + 5bps slip; x2 (card) 0.2% + 10bps slip.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

from bt_cards_common import N_RANDOM, daily_bars, pct_rank, pf, rng, rows, sharpe, summarize, write_json

SLUG = "xs-alt-momentum-weekly"
LOOKBACK, TOP, N_UNI, VOLWIN = 28, 5, 30, 30
COST = {"base": 0.0015, "x2": 0.003}
TRAIN0, OOS0, END = date(2019, 1, 7), date(2023, 1, 1), date(2026, 9, 28)
# card rule is 0.5; `--haircut 1.0` is a sensitivity run (token migrations like MATIC->POL look like delistings)
HAIRCUT = float(sys.argv[sys.argv.index("--haircut") + 1]) if "--haircut" in sys.argv else 0.5
if HAIRCUT != 0.5:
    SLUG += f"-haircut{HAIRCUT}"
EXCL = {
    "BTC", "USDC", "BUSD", "TUSD", "USDP", "PAX", "DAI", "FDUSD", "USDS", "USDSB", "SUSD", "UST", "USTC", "USDE",
    "AEUR", "EUR", "EURI", "GBP", "AUD", "BKRW", "IDRT", "BIDR", "TRY", "BRL", "PAXG", "XAUT", "WBTC", "WBETH",
    "BETH", "USD1", "BFUSD", "RLUSD", "XUSD", "USDJ", "VAI", "ERD_OLD", "BCC", "BCHSV",
}


def base_of(sym: str) -> str:
    return sym[:-4]


def is_excluded(sym: str) -> bool:
    b = base_of(sym)
    return b in EXCL or b.endswith(("UP", "DOWN", "BULL", "BEAR")) and b not in {"JUP", "SUP"}


def main():
    bars = daily_bars("binance_spot_usdt_1d")
    status = {r["symbol"]: r["exchangeinfo_status"] for r in rows("binance_spot_usdt_symbols")}
    btc = bars["BTCUSDT"]
    syms = [s for s in bars if s.endswith("USDT") and not is_excluded(s)]

    def uni_at(M: date) -> list[tuple[str, float]]:
        cand = []
        for s in syms:
            b = bars[s]
            if M not in b or (M - timedelta(1)) not in b or (M - timedelta(LOOKBACK + 1)) not in b:
                continue
            qv = sum(b[x][2] for x in (M - timedelta(i) for i in range(1, VOLWIN + 1)) if x in b)
            cand.append((qv, s))
        top = [s for _, s in sorted(cand, reverse=True)[:N_UNI]]
        return top

    def hold_ret(s: str, M: date) -> float:
        b, x = bars[s], M + timedelta(7)
        if x in b:
            return b[x][0] / b[M][0] - 1
        last = max(dd for dd in b if dd < x)
        return b[last][1] / b[M][0] * HAIRCUT - 1  # delisted / halted during hold: card -50%

    def mom(s: str, M: date, lb: int) -> float | None:
        b = bars[s]
        a, z = M - timedelta(lb + 1), M - timedelta(1)
        return b[z][1] / b[a][1] - 1 if a in b and z in b else None

    mondays = []
    M = TRAIN0
    while M <= END:
        mondays.append(M)
        M += timedelta(7)
    weeks = []
    for M in mondays:
        u = uni_at(M)
        if len(u) < N_UNI:
            continue
        rets = {s: hold_ret(s, M) for s in u}
        picks = {}
        for lb in (21, LOOKBACK, 35):
            ranked = sorted(((mom(s, M, lb), s) for s in u if mom(s, M, lb) is not None), reverse=True)
            picks[lb] = [s for _, s in ranked[:TOP]]
        weeks.append({"M": M, "u": u, "r": rets, "picks": picks})
    print("weeks", len(weeks), file=sys.stderr)

    def run(sel, cost: float) -> list[float]:
        """sel(week) -> list of symbols, equal weight; turnover vs drifted previous weights."""
        out, prev = [], {}
        for w in weeks:
            names = sel(w)
            tgt = {s: 1 / len(names) for s in names}
            keys = set(tgt) | set(prev)
            turn = sum(abs(tgt.get(k, 0) - prev.get(k, 0)) for k in keys)
            g = sum(tgt[s] * w["r"][s] for s in names)
            out.append(g - turn * cost)
            tot = 1 + g
            prev = {s: tgt[s] * (1 + w["r"][s]) / tot for s in names} if tot > 0 else {}
        return out

    idx = lambda a, b: [i for i, w in enumerate(weeks) if a <= w["M"] < b]  # noqa: E731
    I_tr, I_oos = idx(TRAIN0, OOS0), idx(OOS0, END + timedelta(1))
    mid = I_oos[len(I_oos) // 2]
    I_h1, I_h2 = [i for i in I_oos if i < mid], [i for i in I_oos if i >= mid]
    sub = lambda xs, I: [xs[i] for i in I]  # noqa: E731

    res: dict = {"weeks": len(weeks), "oos_weeks": len(I_oos)}
    strat = {k: run(lambda w: w["picks"][LOOKBACK], c) for k, c in COST.items()}
    ew = {k: run(lambda w: w["u"], c) for k, c in COST.items()}
    btc_w = [btc[w["M"] + timedelta(7)][0] / btc[w["M"]][0] - 1 for w in weeks]
    for name, xs in (("strat_base", strat["base"]), ("strat_x2", strat["x2"]), ("ew30_x2", ew["x2"]), ("btc_bh", btc_w)):
        res[name] = {p: {**summarize(sub(xs, I)), "sharpe": sharpe(sub(xs, I), 52)}
                     for p, I in (("full", range(len(weeks))), ("train", I_tr), ("oos", I_oos), ("oos_h1", I_h1), ("oos_h2", I_h2))}
    so, eo = sub(strat["x2"], I_oos), sub(ew["x2"], I_oos)
    res["oos_weekly_winrate_vs_ew_pct"] = round(sum(a > b for a, b in zip(so, eo)) / len(so) * 100, 1)
    for lb in (21, 35):
        xs = sub(run(lambda w, lb=lb: w["picks"][lb], COST["x2"]), I_oos)
        res[f"lookback_{lb}_oos_x2"] = summarize(xs)

    R = rng()
    oos_weeks = [weeks[i] for i in I_oos]
    dist = []
    for _ in range(N_RANDOM):
        draws = {id(w): R.sample(w["u"], TOP) for w in oos_weeks}
        xs, prev = [], {}
        for w in oos_weeks:
            names = draws[id(w)]
            tgt = {s: 1 / TOP for s in names}
            turn = sum(abs(tgt.get(k, 0) - prev.get(k, 0)) for k in set(tgt) | set(prev))
            g = sum(tgt[s] * w["r"][s] for s in names)
            xs.append(g - turn * COST["x2"])
            tot = 1 + g
            prev = {s: tgt[s] * (1 + w["r"][s]) / tot for s in names} if tot > 0 else {}
        eq = 1.0
        for x in xs:
            eq *= 1 + x
        dist.append(eq - 1)
    eq = 1.0
    for x in so:
        eq *= 1 + x
    res["oos_random_pct_x2"] = pct_rank(eq - 1, dist)
    res["random_p95_ret_pct"] = round(sorted(dist)[int(0.95 * N_RANDOM)] * 100, 1)
    res["random_median_ret_pct"] = round(sorted(dist)[N_RANDOM // 2] * 100, 1)
    from collections import Counter
    res["universe_freq_top40"] = Counter(s for w in weeks for s in w["u"]).most_common(40)
    res["delisted_in_universe"] = sorted({s for w in weeks for s in w["u"] if status.get(s) == "BREAK"})
    res["picks_oos"] = [(str(w["M"]), w["picks"][LOOKBACK]) for w in oos_weeks]

    o, why = res["strat_x2"]["oos"], []
    if (o["pf"] or 0) < 1.1:
        why.append(f"OOS weekly PF x2 {o['pf']} < 1.1")
    if res["oos_weekly_winrate_vs_ew_pct"] <= 50:
        why.append(f"OOS weekly win vs EW {res['oos_weekly_winrate_vs_ew_pct']}% <= 50%")
    if (o["sharpe"] or -9) < (res["ew30_x2"]["oos"]["sharpe"] or -9) and (o["sharpe"] or -9) < (res["btc_bh"]["oos"]["sharpe"] or -9):
        why.append("OOS Sharpe below both EW30 and BTC")
    if res["oos_random_pct_x2"] < 95:
        why.append(f"random pct {res['oos_random_pct_x2']} < 95")
    sgn = o["ret_pct"] > 0
    for lb in (21, 35):
        if (res[f"lookback_{lb}_oos_x2"]["ret_pct"] > 0) != sgn:
            why.append(f"lookback {lb} OOS sign flips")
    res["verdict"] = "KILL" if why else "SURVIVE"
    res["reasons"] = why
    path = write_json(SLUG, res)
    for k in ("strat_base", "strat_x2", "ew30_x2", "btc_bh"):
        print(k, res[k])
    print({k: res[k] for k in ("oos_weekly_winrate_vs_ew_pct", "lookback_21_oos_x2", "lookback_35_oos_x2", "oos_random_pct_x2",
                              "random_p95_ret_pct", "random_median_ret_pct", "verdict", "reasons")})
    print(res["universe_freq_top40"])
    print(len(res["delisted_in_universe"]), res["delisted_in_universe"][:40], path)


if __name__ == "__main__":
    main()
