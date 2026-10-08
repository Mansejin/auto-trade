#!/usr/bin/env python3
"""Card weekend-gap-fade-btc-eth (frozen 2026-10-08), encoded as-is.

W = Sunday close (Mon 00:00 UTC) / Saturday open (Sat 00:00 UTC) - 1 on Binance spot, per coin.
W <= -2% -> long at Monday 00:00 open; W >= +2% -> short. Exit Tuesday 00:00 open. No stop.
Execution on Binance perp (Bitget proxy) open-to-open; before the perp exists (BTC < 2019-09-08,
ETH < 2019-11-27) spot open-to-open with zero funding. Funding: settlements t with entry < t <= exit,
long pays rate, short receives. Costs per side: base taker 0.06% + slip 5bps; x2 taker 0.12% + slip 5bps.
Split: train 2018-01..2023-06 / OOS 2023-07..2026-09. Upbit long-only variant reported, not judged.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from bt_cards_common import N_RANDOM, daily_bars, halves, pct_rank, rng, rows, sharpe, summarize, write_json

SLUG = "weekend-gap-fade-btc-eth"
TH = 0.02
COST = {"base": 0.0006 + 0.0005, "x2": 0.0012 + 0.0005}  # per side
UPBIT_COST = {"base": 0.0005 + 0.0005, "x2": 0.0010 + 0.0005}
START, OOS0, ETF0, END = date(2018, 1, 1), date(2023, 7, 1), date(2024, 1, 1), date(2026, 9, 30)
COINS = ("BTCUSDT", "ETHUSDT")
TRANSFER = ("XRPUSDT",)
DAY = timedelta(days=1)


def funding_by_day(sym: str) -> dict:
    """Sum of Binance funding paid on the open-to-open interval (D 00:00, D+1 00:00], keyed by D."""
    out: dict = {}
    for r in rows("funding"):
        if r["exchange"] != "binance" or r["symbol"] != sym:
            continue
        t = datetime.fromisoformat(r["funding_time_utc"].replace("Z", "+00:00"))
        k = (t - timedelta(microseconds=1)).date()
        out[k] = out.get(k, 0.0) + float(r["funding_rate"])
    return out


def day_ret(D: date, side: int, spot: dict, perp: dict, fund: dict, cost: float) -> float | None:
    """Open D -> open D+1 for side (+1 long / -1 short), net of funding and 2x per-side cost."""
    px = perp if D in perp and D + DAY in perp else spot
    if D not in px or D + DAY not in px:
        return None
    f = fund.get(D, 0.0) if px is perp else 0.0
    return side * (px[D + DAY][0] / px[D][0] - 1) - side * f - 2 * cost


def sma200_below(spot: dict, sunday: date) -> bool | None:
    closes = [spot[sunday - timedelta(days=i)][1] for i in range(200) if sunday - timedelta(days=i) in spot]
    return None if len(closes) < 200 else spot[sunday][1] < sum(closes) / 200


def signals(spot: dict, start: date, end: date) -> list[tuple[date, int, float]]:
    """[(monday, side, W)] using only Sat open and Sun close (known at Mon 00:00)."""
    out = []
    m = start + timedelta(days=(7 - start.weekday()) % 7)
    while m <= end:
        sat, sun = m - 2 * DAY, m - DAY
        if sat in spot and sun in spot:
            w = spot[sun][1] / spot[sat][0] - 1
            if w <= -TH:
                out.append((m, 1, w))
            elif w >= TH:
                out.append((m, -1, w))
        m += 7 * DAY
    return out


def stats(trades: list[dict], key: str = "x2") -> dict:
    rs = [t[key] for t in trades]
    s = summarize(rs)
    if rs:
        s["sharpe_per_exp_day"] = sharpe(rs, 365)
        s["n_long"] = sum(t["side"] == 1 for t in trades)
        s["n_short"] = sum(t["side"] == -1 for t in trades)
    return s


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def run_coin(sym: str, fund: dict, spot: dict, perp: dict) -> list[dict]:
    out = []
    for m, side, w in signals(spot, START, END):
        r = {k: day_ret(m, side, spot, perp, fund, c) for k, c in COST.items()}
        if r["x2"] is None:
            continue
        out.append({"sym": sym, "date": m, "side": side, "W": round(w, 4), **r,
                    "perp": m in perp and m + DAY in perp, "below_sma200": sma200_below(spot, m - DAY)})
    return out


def mondays_uncond(spot, perp, fund, side) -> list[float]:
    out, m = [], OOS0 + timedelta(days=(7 - OOS0.weekday()) % 7)
    while m <= END:
        r = day_ret(m, side, spot, perp, fund, COST["x2"])
        if r is not None:
            out.append(r)
        m += 7 * DAY
    return out


def random_dist(data: dict, oos_by: dict) -> list[float]:
    """Same long/short counts per coin, random OOS dates (any weekday), 1-day hold, x2 costs; pooled mean."""
    R = rng()
    pre = {s: [D for D in sorted(data[s][1]) if OOS0 <= D <= END and D + DAY in data[s][1]] for s in data}
    out = []
    for _ in range(N_RANDOM):
        rs = []
        for s, (fund, spot, perp) in data.items():
            for t in oos_by[s]:
                rs.append(day_ret(R.choice(pre[s]), t["side"], spot, perp, fund, COST["x2"]))
        out.append(sum(rs) / len(rs))
    return out


def weekly_portfolio(trades: list[dict], key: str) -> list[float]:
    """50:50 BTC/ETH sleeves: each Monday, mean over coins (no-trade coin contributes 0)."""
    by: dict = {}
    for t in trades:
        by.setdefault(t["date"], {})[t["sym"]] = t[key]
    return [sum(v.values()) / len(COINS) for _, v in sorted(by.items())]


def upbit_variant() -> dict:
    bars = daily_bars("upbit_krw_1d", key="market", only={"KRW-BTC", "KRW-ETH"})
    res = {}
    allt = []
    for mk, b in bars.items():
        for m, side, w in signals(b, START, END):
            if side != 1 or m not in b or m + DAY not in b:
                continue
            g = b[m + DAY][0] / b[m][0] - 1
            allt.append({"sym": mk, "date": m, "side": 1, "W": w, "below_sma200": sma200_below(b, m - DAY),
                         **{k: g - 2 * c for k, c in UPBIT_COST.items()}})
    allt.sort(key=lambda t: t["date"])
    oos = [t for t in allt if t["date"] >= OOS0]
    res["full_base"], res["full_x2"] = stats(allt, "base"), stats(allt)
    res["train_x2"] = stats([t for t in allt if t["date"] < OOS0])
    res["oos_base"], res["oos_x2"] = stats(oos, "base"), stats(oos)
    res["etf_x2"] = stats([t for t in allt if t["date"] >= ETF0])
    res["oos_below_sma200_x2"] = stats([t for t in oos if t["below_sma200"]])
    res["oos_above_sma200_x2"] = stats([t for t in oos if t["below_sma200"] is False])
    res["full_below_sma200_x2"] = stats([t for t in allt if t["below_sma200"]])
    for mk in bars:
        res[f"oos_{mk}_x2"] = stats([t for t in oos if t["sym"] == mk])
    return res


def main():
    spot = daily_bars("binance_spot_1d", only=set(COINS + TRANSFER))
    perp = daily_bars("binance_perp_1d", only=set(COINS + TRANSFER))
    data = {s: (funding_by_day(s), spot[s], perp[s]) for s in COINS}
    trades = sorted((t for s in COINS for t in run_coin(s, *data[s])), key=lambda t: (t["date"], t["sym"]))
    oos = [t for t in trades if t["date"] >= OOS0]
    train = [t for t in trades if t["date"] < OOS0]
    etf = [t for t in trades if t["date"] >= ETF0]
    oos_by = {s: [t for t in oos if t["sym"] == s] for s in COINS}

    res: dict = {"card": f"docs/research/cards/{SLUG}.md", "cost_per_side": COST,
                 "periods": {"train": [str(START), str(OOS0 - DAY)], "oos": [str(OOS0), str(END)], "etf": [str(ETF0), str(END)]}}
    for k in ("base", "x2"):
        res[f"full_{k}"], res[f"train_{k}"], res[f"oos_{k}"], res[f"etf_{k}"] = (stats(x, k) for x in (trades, train, oos, etf))
    h1, h2 = halves(trades, lambda t: t["date"])
    o1, o2 = halves(oos, lambda t: t["date"])
    res["full_h1_x2"], res["full_h2_x2"], res["oos_h1_x2"], res["oos_h2_x2"] = (stats(x) for x in (h1, h2, o1, o2))
    res["pre_perp_trades"] = sum(not t["perp"] for t in trades)
    for s in COINS:
        res[f"oos_{s}_x2"], res[f"oos_{s}_base"] = stats(oos_by[s]), stats(oos_by[s], "base")
        res[f"full_{s}_x2"] = stats([t for t in trades if t["sym"] == s])
    res["oos_long_x2"] = stats([t for t in oos if t["side"] == 1])
    res["oos_short_x2"] = stats([t for t in oos if t["side"] == -1])
    res["sma200_report_only"] = {
        "oos_below_x2": stats([t for t in oos if t["below_sma200"]]),
        "oos_above_x2": stats([t for t in oos if t["below_sma200"] is False]),
        "full_below_x2": stats([t for t in trades if t["below_sma200"]]),
        "full_above_x2": stats([t for t in trades if t["below_sma200"] is False]),
    }
    res["portfolio_weekly_x2"] = {"full": summarize(weekly_portfolio(trades, "x2")), "oos": summarize(weekly_portfolio(oos, "x2"))}

    # benchmarks
    oos_mean = mean([t["x2"] for t in oos])
    mon = {}
    for side, nm in ((1, "long"), (-1, "short")):
        rs = [r for s in COINS for r in mondays_uncond(data[s][1], data[s][2], data[s][0], side)]
        mon[nm] = {"n": len(rs), "mean_pct": round(mean(rs) * 100, 3)}
    res["monday_uncond_oos_x2"] = mon
    bh = [spot["BTCUSDT"][D + DAY][0] / spot["BTCUSDT"][D][0] - 1
          for D in sorted(spot["BTCUSDT"]) if OOS0 <= D <= END and D + DAY in spot["BTCUSDT"]]
    res["btc_bh_oos_per_day"] = {"n": len(bh), "mean_pct": round(mean(bh) * 100, 3), "sharpe": sharpe(bh, 365)}
    dist = random_dist(data, oos_by)
    res["random_oos_x2"] = {"pct_rank": pct_rank(oos_mean, dist), "p50_pct": round(sorted(dist)[N_RANDOM // 2] * 100, 3),
                            "p95_pct": round(sorted(dist)[int(0.95 * N_RANDOM)] * 100, 3)}
    yrs = ((END - OOS0).days + 1) / 365.25
    res["oos_trades_per_year"] = round(len(oos) / yrs, 1)

    # transfer (info only; card locks universe to BTC/ETH)
    xr = []
    xf = funding_by_day("XRPUSDT")
    for m, side, w in signals(spot["XRPUSDT"], START, END):
        r = day_ret(m, side, spot["XRPUSDT"], perp["XRPUSDT"], xf, COST["x2"])
        if r is not None:
            xr.append({"date": m, "side": side, "x2": r})
    res["transfer_XRPUSDT_info"] = {"full_x2": stats(xr), "oos_x2": stats([t for t in xr if t["date"] >= OOS0])}

    res["upbit_long_only_report"] = upbit_variant()

    # pre-registered criteria (binding at x2 costs; base shown in report)
    o = res["oos_x2"]
    crit = []

    def c(name, value, ok, kill=True):
        crit.append({"criterion": name, "value": value, "pass": ok, "kills": kill})

    c("OOS 거래당 평균 > 0 (x2)", o["mean_pct"], o["mean_pct"] > 0)
    c("OOS PF >= 1.1 (x2+slip+funding)", o["pf"], (o["pf"] or 0) >= 1.1)
    c("전체 거래 >= 30", len(trades), len(trades) >= 30, kill=False)
    c("OOS 연환산 거래 >= 24 (빈도 표기)", res["oos_trades_per_year"], res["oos_trades_per_year"] >= 24, kill=False)
    c("무작위 1,000회 95백분위 이상", res["random_oos_x2"]["pct_rank"], res["random_oos_x2"]["pct_rank"] >= 95)
    lo = min(mon["long"]["mean_pct"], mon["short"]["mean_pct"])
    c("월요일 무조건 롱·숏 둘 다보다 낮지 않음", {"strategy": o["mean_pct"], **{k: v["mean_pct"] for k, v in mon.items()}},
      o["mean_pct"] >= lo)
    c("ETF 이후(2024-01~) 평균 > 0 (x2)", res["etf_x2"]["mean_pct"], res["etf_x2"]["mean_pct"] > 0)
    signs = {s: res[f"oos_{s}_x2"]["mean_pct"] for s in COINS}
    c("BTC·ETH OOS 평균 부호 둘 다 양수 (x2)", signs, all(v > 0 for v in signs.values()))
    b = res["btc_bh_oos_per_day"]
    sh = o["sharpe_per_exp_day"] or -math.inf
    c("노출일당 수익·Sharpe가 BTC B&H 이상", {"strategy": [o["mean_pct"], o["sharpe_per_exp_day"]], "bh": [b["mean_pct"], b["sharpe"]]},
      o["mean_pct"] >= b["mean_pct"] and sh >= b["sharpe"])
    res["criteria"] = crit
    fails = [x["criterion"] for x in crit if x["kills"] and not x["pass"]]
    res["verdict"] = "INCONCLUSIVE" if len(trades) < 30 else ("KILL" if fails else "SURVIVE")
    res["reasons"] = fails
    res["n_trades"] = {"full": len(trades), "train": len(train), "oos": len(oos), "etf": len(etf)}
    res["trades"] = [{k: (round(v, 5) if isinstance(v, float) else v) for k, v in t.items()} for t in trades]

    assert all(t["date"].weekday() == 0 for t in trades), "entries must be Mondays"
    assert all((t["W"] <= -TH) == (t["side"] == 1) for t in trades), "side must fade W"

    path = write_json(SLUG, res)
    for k in ("full_base", "full_x2", "train_x2", "oos_base", "oos_x2", "etf_x2", "full_h1_x2", "full_h2_x2",
              "oos_h1_x2", "oos_h2_x2", "oos_long_x2", "oos_short_x2", "portfolio_weekly_x2",
              "monday_uncond_oos_x2", "btc_bh_oos_per_day", "random_oos_x2", "oos_trades_per_year",
              "sma200_report_only", "transfer_XRPUSDT_info", "pre_perp_trades", "n_trades"):
        print(k, res[k])
    for s in COINS:
        print(s, res[f"oos_{s}_x2"], res[f"oos_{s}_base"], res[f"full_{s}_x2"])
    print("upbit", res["upbit_long_only_report"])
    for x in crit:
        print(x)
    print(res["verdict"], res["reasons"], path)


if __name__ == "__main__":
    main()
