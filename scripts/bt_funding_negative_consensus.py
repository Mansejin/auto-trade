#!/usr/bin/env python3
"""Card funding-negative-consensus (frozen 2026-10-08), encoded as-is.

Signal day D (UTC): mean of Binance funding settlements dated D <= -0.005% AND same for Bybit.
All three settlements (00/08/16 UTC) are known before D+1 00:00 UTC = Upbit 09:00 KST open.
Entry: Upbit KRW-BTC open D+1. Exit: open D+4 (3 days). Non-overlapping (signals while holding ignored).
Costs: base 10bps fee + 5bps slip round trip; stress (card) 20bps fee + 10bps slip.
"""
from __future__ import annotations

from datetime import date, timedelta

from bt_cards_common import N_RANDOM, daily_bars, d, halves, pct_rank, rng, rows, summarize, write_json

SLUG = "funding-negative-consensus"
TH, HOLD = -0.00005, 3
COST = {"base": 0.0015, "x2": 0.0030}
OOS0, TRAIN0, END = date(2023, 7, 1), date(2020, 3, 1), date(2026, 9, 30)


def daily_funding(sym: str) -> dict:
    acc: dict = {}
    for r in rows("funding"):
        if r["symbol"] == sym:
            acc.setdefault((r["exchange"], d(r["funding_time_utc"])), []).append(float(r["funding_rate"]))
    return {k: sum(v) / len(v) for k, v in acc.items()}


def signals(fund: dict, exchanges: tuple) -> list[date]:
    days = sorted({k[1] for k in fund})
    return [D for D in days if all((ex, D) in fund and fund[(ex, D)] <= TH for ex in exchanges)]


def trades(sig_days: list[date], bars: dict) -> list[dict]:
    out, free_from = [], date.min
    for D in sig_days:
        e, x = D + timedelta(1), D + timedelta(1 + HOLD)
        if e < free_from or e not in bars or x not in bars or not (TRAIN0 <= e <= END):
            continue
        out.append({"signal": D, "entry": e, "exit": x, "gross": bars[x][0] / bars[e][0] - 1})
        free_from = x
    return out


def stats(tr: list[dict], cost: float) -> dict:
    return summarize([t["gross"] - cost for t in tr])


def bh_per_day(bars: dict, a: date, b: date) -> float:
    ds = [x for x in sorted(bars) if a <= x <= b]
    return (bars[ds[-1]][0] / bars[ds[0]][0]) ** (1 / (len(ds) - 1)) - 1, (bars[ds[-1]][0] / bars[ds[0]][0] - 1)


def random_means(bars: dict, n: int, a: date, b: date, cost: float) -> list[float]:
    pool = [x for x in sorted(bars) if a <= x <= b and x + timedelta(HOLD) in bars]
    R = rng()
    return [sum(bars[e + timedelta(HOLD)][0] / bars[e][0] - 1 - cost for e in R.sample(pool, n)) / n for _ in range(N_RANDOM)]


def run(asset: str, upbit_mkt: str) -> dict:
    fund = daily_funding(f"{asset}USDT")
    bars = daily_bars("upbit_krw_1d", key="market", only={upbit_mkt})[upbit_mkt]
    res: dict = {}
    for name, exs in {"consensus": ("binance", "bybit"), "binance_only": ("binance",), "bybit_only": ("bybit",)}.items():
        tr = trades(signals(fund, exs), bars)
        tr_is = [t for t in tr if t["entry"] < OOS0]
        tr_oos = [t for t in tr if t["entry"] >= OOS0]
        h1, h2 = halves(tr_oos, lambda t: t["entry"])
        res[name] = {
            "full": stats(tr, COST["base"]), "train": stats(tr_is, COST["base"]), "oos": stats(tr_oos, COST["base"]),
            "oos_x2": stats(tr_oos, COST["x2"]), "full_x2": stats(tr, COST["x2"]),
            "oos_h1_x2": stats(h1, COST["x2"]), "oos_h2_x2": stats(h2, COST["x2"]),
            "trades": [{k: str(v) if isinstance(v, date) else round(v, 5) for k, v in t.items()} for t in tr],
        }
        if name == "consensus":
            n_oos = len(tr_oos)
            bh_d, bh_tot = bh_per_day(bars, OOS0, END)
            mean_x2 = sum(t["gross"] - COST["x2"] for t in tr_oos) / n_oos if n_oos else 0.0
            dist = random_means(bars, n_oos, OOS0, END, COST["x2"]) if n_oos else []
            res[name]["oos_bh"] = {"bh_ret_pct": round(bh_tot * 100, 1), "bh_per_day_pct": round(bh_d * 100, 4),
                                   "strat_per_held_day_pct_x2": round(((1 + mean_x2) ** (1 / HOLD) - 1) * 100, 4)}
            res[name]["oos_random_pct_x2"] = pct_rank(mean_x2, dist) if dist else None
            res[name]["random_p95_mean_pct"] = round(sorted(dist)[int(0.95 * N_RANDOM)] * 100, 3) if dist else None
    return res


def verdict(r: dict) -> tuple[str, list[str]]:
    c = r["consensus"]
    why = []
    if c["full"].get("n", 0) < 30:
        why.append(f"trades {c['full'].get('n', 0)} < 30 -> INCONCLUSIVE")
    if c["oos"].get("n", 0) == 0:
        return "INCONCLUSIVE", why + ["no OOS trades"]
    if c["oos"]["mean_pct"] <= 0:
        why.append("OOS mean <= 0")
    if (c["oos_x2"]["pf"] or 0) < 1.1:
        why.append(f"OOS PF x2 {c['oos_x2']['pf']} < 1.1")
    if c["oos_random_pct_x2"] < 95:
        why.append(f"random pct {c['oos_random_pct_x2']} < 95")
    if c["oos_bh"]["strat_per_held_day_pct_x2"] <= c["oos_bh"]["bh_per_day_pct"]:
        why.append("per-exposure-day return <= B&H")
    s = lambda k: (r[k]["oos"].get("mean_pct") or 0) > 0  # noqa: E731
    if not (s("binance_only") == s("bybit_only") == s("consensus")):
        why.append("single-source OOS sign mismatch")
    if c["full"]["n"] < 30:  # sample gate first: kill tests on a handful of OOS trades are not informative
        return "INCONCLUSIVE", why
    return ("KILL" if why else "SURVIVE"), why


if __name__ == "__main__":
    out = {"card": SLUG, "btc": run("BTC", "KRW-BTC"), "transfer_eth": run("ETH", "KRW-ETH")}
    out["verdict"], out["reasons"] = verdict(out["btc"])
    out["transfer_eth_verdict"] = verdict(out["transfer_eth"])
    p = write_json(SLUG, out)
    for a in ("btc", "transfer_eth"):
        for k, v in out[a].items():
            print(a, k, {kk: vv for kk, vv in v.items() if kk != "trades"})
    print(out["verdict"], out["reasons"], "->", p)
