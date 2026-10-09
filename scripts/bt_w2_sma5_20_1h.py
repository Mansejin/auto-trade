#!/usr/bin/env python3
"""Card w2-bitget-sma5-20-1h (frozen 2026-10-10), encoded as-is from the live w2 bot.

Signals use bot.indicators.sma + bot.signals cross helpers on closed 1h bars (bar i).
Fill at open of bar i+1. Long only. Exits checked on closed bar i in bot order:
SL (close_i vs signal-bar close <= -3%), TP (>= +6%), then SMA5 cross_below SMA20.
Funding: Binance settlements t with entry < t <= exit, long pays. Costs per side:
base taker 0.06%; x2 taker 0.12% + slip 5bps. Split train 2019-09..2023-06 / OOS 2023-07..2026-09.
Shared-account skip (w5 holding) is not modelled.
"""
from __future__ import annotations

import bisect
import math
import sys
from datetime import datetime, timezone

from bt_cards_common import N_RANDOM, ROOT, halves, pct_rank, rng, rows, sharpe, summarize, write_json

sys.path.insert(0, str(ROOT))
from bot.indicators import sma  # noqa: E402
from bot.signals import _cross_above, _cross_below  # noqa: E402

SLUG = "w2-bitget-sma5-20-1h"
FAST, SLOW, SL, TP = 5, 20, 3.0, 6.0
COST = {"base": 0.0006, "x2": 0.0012 + 0.0005}
H = 3_600_000
OOS0 = int(datetime(2023, 7, 1, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
YEAR_H = 8760


def bars(sym: str):
    t, o, c = [], [], []
    for r in rows("binance_perp_1h"):
        if r["symbol"] == sym:
            t.append(int(r["open_time_ms"])); o.append(float(r["open"])); c.append(float(r["close"]))
    return t, o, c


def funding(sym: str):
    fs = sorted((int(r["funding_time_ms"]), float(r["funding_rate"])) for r in rows("funding")
                if r["exchange"] == "binance" and r["symbol"] == sym)
    ts = [x[0] for x in fs]
    cum = [0.0]
    for _, f in fs:
        cum.append(cum[-1] + f)
    return lambda a, b: cum[bisect.bisect_right(ts, b)] - cum[bisect.bisect_right(ts, a)]  # sum over (a, b]


def trade_ret(t, o, fund, e: int, x: int, c: float) -> float:
    return o[x] / o[e] - 1 - fund(t[e], t[x]) - 2 * c


def simulate(t, o, c, fund) -> list[dict]:
    f, s = sma(c, FAST), sma(c, SLOW)
    out, pos = [], None
    for i in range(SLOW, len(c) - 1):
        if t[i + 1] >= END and pos is None:
            break
        if pos is not None:
            ch = (c[i] - pos["ref"]) / pos["ref"] * 100
            why = "sl" if ch <= -SL else "tp" if ch >= TP else "cross" if _cross_below(f[i - 1], f[i], s[i - 1], s[i]) else None
            if why:
                e, x = pos["e"], i + 1
                out.append({"t": t[e], "e": e, "x": x, "hours": (t[x] - t[e]) / H, "exit": why,
                            **{k: trade_ret(t, o, fund, e, x, v) for k, v in COST.items()}})
                assert why != "sl" or ch <= -SL
                pos = None
            continue
        if _cross_above(f[i - 1], f[i], s[i - 1], s[i]) and t[i + 1] < END:
            pos = {"e": i + 1, "ref": c[i]}
    return out


def stats(tr: list[dict], key: str = "x2") -> dict:
    s = summarize([x[key] for x in tr])
    if tr:
        s["exits"] = {k: sum(x["exit"] == k for x in tr) for k in ("sl", "tp", "cross")}
        s["mean_hours"] = round(sum(x["hours"] for x in tr) / len(tr), 1)
    return s


def per_year(tr: list[dict], a: int, b: int) -> float:
    return round(len(tr) / ((b - a) / H / YEAR_H), 1)


def exposure_hours(t, o, fund, tr: list[dict], c: float) -> list[float]:
    """Hourly open-to-open returns while held, funding per hour, cost at first and last hour."""
    out = []
    for x in tr:
        hs = [o[k + 1] / o[k] - 1 - fund(t[k], t[k + 1]) for k in range(x["e"], x["x"])]
        if hs:
            hs[0] -= c; hs[-1] -= c
        out += hs
    return out


def bh_hours(t, o, fund) -> list[float]:
    return [o[k + 1] / o[k] - 1 - fund(t[k], t[k + 1]) for k in range(len(t) - 1) if OOS0 <= t[k] and t[k + 1] <= END]


def random_dist(t, o, fund, oos: list[dict]) -> list[float]:
    R = rng()
    lo = bisect.bisect_left(t, OOS0)
    hi = bisect.bisect_left(t, END)
    dist = []
    for _ in range(N_RANDOM):
        rs = []
        for x in oos:
            n = x["x"] - x["e"]
            e = R.randrange(lo, hi - n)
            rs.append(trade_ret(t, o, fund, e, e + n, COST["x2"]))
        dist.append(sum(rs) / len(rs))
    return dist


def gaps(t) -> int:
    return sum(t[k + 1] - t[k] != H for k in range(len(t) - 1))


def run(sym: str) -> tuple[dict, list[dict], tuple]:
    t, o, c = bars(sym)
    fund = funding(sym)
    tr = simulate(t, o, c, fund)
    train = [x for x in tr if x["t"] < OOS0]
    oos = [x for x in tr if x["t"] >= OOS0]
    res = {"bars": len(t), "first": t[0], "gaps": gaps(t)}
    for k in COST:
        res[f"full_{k}"], res[f"train_{k}"], res[f"oos_{k}"] = stats(tr, k), stats(train, k), stats(oos, k)
    h1, h2 = halves(tr, lambda x: x["t"])
    o1, o2 = halves(oos, lambda x: x["t"])
    res["full_h1_x2"], res["full_h2_x2"], res["oos_h1_x2"], res["oos_h2_x2"] = (stats(x) for x in (h1, h2, o1, o2))
    res["trades_per_year"] = {"full": per_year(tr, t[0], END), "oos": per_year(oos, OOS0, END)}
    yearly = {}
    for x in tr:
        yearly.setdefault(datetime.fromtimestamp(x["t"] / 1000, tz=timezone.utc).year, []).append(x)
    res["by_year_x2"] = {y: stats(v) for y, v in sorted(yearly.items())}
    return res, tr, (t, o, fund)


def main():
    btc, tr, (t, o, fund) = run("BTCUSDT")
    eth, eth_tr, _ = run("ETHUSDT")
    oos = [x for x in tr if x["t"] >= OOS0]

    res: dict = {"card": f"docs/research/cards/{SLUG}.md", "cost_per_side": COST, "rules": {"fast": FAST, "slow": SLOW, "sl": SL, "tp": TP},
                 "periods": {"train": ["2019-09-08", "2023-06-30"], "oos": ["2023-07-01", "2026-09-30"]}, "BTCUSDT": btc}
    res["ETHUSDT_transfer"] = {k: eth[k] for k in ("full_x2", "train_x2", "oos_x2", "oos_base", "oos_h1_x2", "oos_h2_x2", "trades_per_year")}

    exp = exposure_hours(t, o, fund, oos, COST["x2"])
    bh = bh_hours(t, o, fund)
    res["exposure_vs_bh_oos"] = {
        "strategy": {"hours": len(exp), "share_of_time": round(len(exp) / len(bh), 3),
                     "mean_pct_per_h": round(sum(exp) / len(exp) * 100, 4), "sharpe": sharpe(exp, YEAR_H)},
        "bh": {"hours": len(bh), "mean_pct_per_h": round(sum(bh) / len(bh) * 100, 4), "sharpe": sharpe(bh, YEAR_H),
               "ret_pct": round((o[bisect.bisect_left(t, END)] / o[bisect.bisect_left(t, OOS0)] - 1) * 100, 1)},
    }
    dist = random_dist(t, o, fund, oos)
    om = btc["oos_x2"]["mean_pct"] / 100
    sd = sorted(dist)
    res["random_oos_x2"] = {"pct_rank": pct_rank(om, dist), "p50_pct": round(sd[N_RANDOM // 2] * 100, 3),
                            "p95_pct": round(sd[int(0.95 * N_RANDOM)] * 100, 3)}

    o_ = btc["oos_x2"]
    e, b = res["exposure_vs_bh_oos"]["strategy"], res["exposure_vs_bh_oos"]["bh"]
    crit = []

    def c(name, value, ok, kill=True):
        crit.append({"criterion": name, "value": value, "pass": ok, "kills": kill})

    c("1. OOS PF >= 1.1 (x2+slip+funding)", o_["pf"], (o_["pf"] or 0) >= 1.1)
    c("2. OOS 거래당 평균 > 0 (x2)", o_["mean_pct"], o_["mean_pct"] > 0)
    c("3. 전체 거래 >= 30", btc["full_x2"]["n"], btc["full_x2"]["n"] >= 30, kill=False)
    c("4. 무작위 1,000회 95백분위 이상", res["random_oos_x2"]["pct_rank"], res["random_oos_x2"]["pct_rank"] >= 95)
    c("5. 노출 시간당 평균·Sharpe >= BTC B&H", {"strategy": [e["mean_pct_per_h"], e["sharpe"]], "bh": [b["mean_pct_per_h"], b["sharpe"]]},
      e["mean_pct_per_h"] >= b["mean_pct_per_h"] and (e["sharpe"] or -math.inf) >= b["sharpe"])
    c("6. ETH 전이 OOS 평균 > 0 (x2)", eth["oos_x2"]["mean_pct"], eth["oos_x2"]["mean_pct"] > 0)
    res["criteria"] = crit
    fails = [x["criterion"] for x in crit if x["kills"] and not x["pass"]]
    res["verdict"] = "INCONCLUSIVE" if btc["full_x2"]["n"] < 30 else ("KILL" if fails else "SURVIVE")
    res["reasons"] = fails
    res["trades"] = [{"t": datetime.fromtimestamp(x["t"] / 1000, tz=timezone.utc).isoformat()[:16], "hours": x["hours"], "exit": x["exit"],
                      "base": round(x["base"], 5), "x2": round(x["x2"], 5)} for x in tr]

    path = write_json(SLUG, res)
    for k, v in btc.items():
        print(k, v)
    print("ETH", res["ETHUSDT_transfer"])
    print("exposure", res["exposure_vs_bh_oos"])
    print("random", res["random_oos_x2"])
    for x in crit:
        print(x)
    print(res["verdict"], res["reasons"], path)


if __name__ == "__main__":
    main()
