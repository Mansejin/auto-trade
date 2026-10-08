#!/usr/bin/env python3
"""Card oi-flush-rebound (frozen 2026-10-08, pre-test addendum same day), encoded as-is.

Signal day D (UTC): dOI_D = oi(D+1 00:00)/oi(D 00:00) - 1 <= coin's train 5th percentile AND Binance perp
D return (close/open - 1) < 0. Long at D+1 00:00 open, exit 2 days later at open (D+3). No stop, non-overlapping
per coin. Threshold computed once on train (2021-12-02..2023-06-30), never recomputed in OOS (2023-07..2026-09).
Addendum: common start 2021-12-02, coin-quantity `oi`, snapshots with stale_min > 60 -> dOI missing (see STALE),
stored (+5 min corrected) timestamps used as-is.
Primary execution: Upbit KRW spot open-to-open (card: entry = Upbit 09:00 KST open), per side 0.05% (x2 0.10%)
+ slip 5bps (SOL 10bps). Bitget-proxy: Binance perp open-to-open, per side 0.06% (x2 0.12%) + slip, funding paid.
Price-only control: same rule with "D return <= train 5th percentile of D returns" only.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from bt_cards_common import N_RANDOM, d, daily_bars, halves, pct_rank, rng, rows, sharpe, summarize, write_json

SLUG = "oi-flush-rebound"
Q, HOLD = 0.05, 2
START, OOS0, END = date(2021, 12, 2), date(2023, 7, 1), date(2026, 9, 30)
COINS = ("BTC", "ETH", "SOL")
SLIP = {"BTC": 0.0005, "ETH": 0.0005, "SOL": 0.0010}
FEE = {"upbit": {"base": 0.0005, "x2": 0.0010}, "perp": {"base": 0.0006, "x2": 0.0012}}
DAY = timedelta(days=1)


def quantile(xs: list[float], q: float) -> float:
    """Linear interpolation (numpy default)."""
    s = sorted(xs)
    i = q * (len(s) - 1)
    lo = math.floor(i)
    return s[lo] + (s[min(lo + 1, len(s) - 1)] - s[lo]) * (i - lo)


def load_doi(col: str = "oi") -> tuple[dict, dict]:
    """{coin: {D: dOI_D}} with stale handling; also the stale dates per coin."""
    oi, stale = {}, {}
    for r in rows("binance_oi_1d"):
        c = r["symbol"].replace("USDT", "")
        D = d(r["date_utc"])
        if c not in COINS or D < START:
            continue
        oi.setdefault(c, {})[D] = float(r[col])
        if int(r["stale_min"]) > 60:
            stale.setdefault(c, set()).add(D)
    out = {}
    for c, s in oi.items():
        bad = set()
        # addendum: stale day S and the next day are missing; dOI_{S-1} also ends on the stale snapshot -> drop too
        for S in stale.get(c, ()):
            bad |= {S - DAY, S, S + DAY}
        out[c] = {D: s[D + DAY] / s[D] - 1 for D in s if D + DAY in s and D not in bad}
    return out, {c: sorted(str(x) for x in v) for c, v in stale.items()}


def funding_by_day(sym: str) -> dict:
    out: dict = {}
    for r in rows("funding"):
        if r["exchange"] != "binance" or r["symbol"] != sym:
            continue
        t = datetime.fromisoformat(r["funding_time_utc"].replace("Z", "+00:00"))
        k = (t - timedelta(microseconds=1)).date()
        out[k] = out.get(k, 0.0) + float(r["funding_rate"])
    return out


def sma200_below(bars: dict, D: date) -> bool | None:
    cl = [bars[D - i * DAY][1] for i in range(200) if D - i * DAY in bars]
    return None if len(cl) < 200 else bars[D][1] < sum(cl) / 200


def trade_ret(E: date, bars: dict, fee: float, slip: float, fund: dict | None) -> float | None:
    X = E + HOLD * DAY
    if E not in bars or X not in bars:
        return None
    f = sum(fund.get(E + i * DAY, 0.0) for i in range(HOLD)) if fund is not None else 0.0
    return bars[X][0] / bars[E][0] - 1 - f - 2 * (fee + slip)


def run(sig_days: dict, venue: str, bars: dict, fund: dict) -> list[dict]:
    """sig_days {coin: sorted signal dates D}. Non-overlap: next entry only at/after previous exit."""
    out = []
    for c in COINS:
        free = date.min
        for D in sig_days[c]:
            E = D + DAY
            if E < free:
                continue
            fd = fund.get(c) if venue == "perp" else None
            r = {k: trade_ret(E, bars[c], f, SLIP[c], fd) for k, f in FEE[venue].items()}
            if r["x2"] is None:
                continue
            out.append({"sym": c, "date": D, **r, "below_sma200": sma200_below(bars[c], D)})
            free = E + HOLD * DAY
    return sorted(out, key=lambda t: (t["date"], t["sym"]))


def stats(trades: list[dict], key: str = "x2") -> dict:
    rs = [t[key] for t in trades]
    s = summarize(rs)
    if rs:
        s["mean_per_exp_day_pct"] = round(sum(rs) / len(rs) / HOLD * 100, 3)
        s["sharpe_per_exp_day"] = sharpe([r / HOLD for r in rs], 365 / HOLD) if len(rs) > 1 else None
    return s


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def random_dist(oos_by: dict, bars: dict, venue: str, fund: dict) -> list[float]:
    R = rng()
    fee = FEE[venue]["x2"]
    pre = {c: [D for D in sorted(bars[c]) if OOS0 <= D <= END and D + (HOLD + 1) * DAY in bars[c]] for c in COINS}
    out = []
    for _ in range(N_RANDOM):
        rs = []
        for c in COINS:
            fd = fund.get(c) if venue == "perp" else None
            rs += [trade_ret(R.choice(pre[c]) + DAY, bars[c], fee, SLIP[c], fd) for _ in oos_by[c]]
        out.append(sum(rs) / len(rs))
    return out


def bh(bars: dict) -> dict:
    """OOS buy & hold daily open-to-open, per coin and equal-weight basket."""
    res, basket = {}, {}
    for c in COINS:
        b = bars[c]
        rs = [(D, b[D + DAY][0] / b[D][0] - 1) for D in sorted(b) if OOS0 <= D <= END and D + DAY in b]
        res[c] = {"n": len(rs), "mean_pct": round(mean([r for _, r in rs]) * 100, 3), "sharpe": sharpe([r for _, r in rs], 365)}
        for D, r in rs:
            basket.setdefault(D, []).append(r)
    br = [mean(v) for _, v in sorted(basket.items())]
    res["basket"] = {"n": len(br), "mean_pct": round(mean(br) * 100, 3), "sharpe": sharpe(br, 365)}
    return res


def evaluate(trades, ctrl, bars, venue, fund) -> dict:
    train = [t for t in trades if t["date"] < OOS0]
    oos = [t for t in trades if t["date"] >= OOS0]
    oos_by = {c: [t for t in oos if t["sym"] == c] for c in COINS}
    res = {"n_trades": {"full": len(trades), "train": len(train), "oos": len(oos),
                        **{f"oos_{c}": len(oos_by[c]) for c in COINS},
                        **{f"train_{c}": sum(t["sym"] == c for t in train) for c in COINS}}}
    for k in ("base", "x2"):
        res[f"full_{k}"], res[f"train_{k}"], res[f"oos_{k}"] = (stats(x, k) for x in (trades, train, oos))
    h1, h2 = halves(trades, lambda t: t["date"])
    o1, o2 = halves(oos, lambda t: t["date"])
    res["full_h1_x2"], res["full_h2_x2"], res["oos_h1_x2"], res["oos_h2_x2"] = (stats(x) for x in (h1, h2, o1, o2))
    for c in COINS:
        res[f"oos_{c}_x2"], res[f"train_{c}_x2"] = stats(oos_by[c]), stats([t for t in train if t["sym"] == c])
    res["sma200_report_only"] = {
        "oos_below_x2": stats([t for t in oos if t["below_sma200"]]),
        "oos_above_x2": stats([t for t in oos if t["below_sma200"] is False]),
        "full_below_x2": stats([t for t in trades if t["below_sma200"]]),
        "full_above_x2": stats([t for t in trades if t["below_sma200"] is False]),
    }
    co = [t for t in ctrl if t["date"] >= OOS0]
    res["price_only_control"] = {"full_x2": stats(ctrl), "train_x2": stats([t for t in ctrl if t["date"] < OOS0]),
                                 "oos_x2": stats(co), **{f"oos_{c}_x2": stats([t for t in co if t["sym"] == c]) for c in COINS}}
    res["bh_oos"] = bh(bars)
    dist = random_dist(oos_by, bars, venue, fund)
    om = mean([t["x2"] for t in oos])
    res["random_oos_x2"] = {"pct_rank": pct_rank(om, dist), "p50_pct": round(sorted(dist)[N_RANDOM // 2] * 100, 3),
                            "p95_pct": round(sorted(dist)[int(0.95 * N_RANDOM)] * 100, 3)}
    res["oos_trades_per_year"] = round(len(oos) / (((END - OOS0).days + 1) / 365.25), 1)

    o, crit = res["oos_x2"], []

    def c(name, value, ok, kill=True):
        crit.append({"criterion": name, "value": value, "pass": bool(ok), "kills": kill})

    c("OOS 거래당 평균 > 0 (x2)", o.get("mean_pct"), (o.get("mean_pct") or -1) > 0)
    c("OOS PF >= 1.1 (x2+slip)", o.get("pf"), (o.get("pf") or 0) >= 1.1)
    c("전체 거래 >= 30", len(trades), len(trades) >= 30, kill=False)
    c("OOS 연환산 거래 >= 24 (빈도 표기)", res["oos_trades_per_year"], res["oos_trades_per_year"] >= 24, kill=False)
    c("무작위 1,000회 95백분위 이상", res["random_oos_x2"]["pct_rank"], res["random_oos_x2"]["pct_rank"] >= 95)
    pm = res["price_only_control"]["oos_x2"].get("mean_pct")
    c("OOS 평균 > 가격만 버전 OOS 평균 (OI 정보)", {"oi_rule": o.get("mean_pct"), "price_only": pm},
      pm is not None and (o.get("mean_pct") or -9) > pm)
    signs = {k: res[f"oos_{k}_x2"].get("mean_pct") for k in COINS}
    c("코인 OOS 평균 음수 2개 미만", signs, sum((v or 0) <= 0 for v in signs.values()) < 2)
    b = res["bh_oos"]["basket"]
    sh = o.get("sharpe_per_exp_day") or -math.inf
    c("노출일당 수익·Sharpe >= B&H(3코인 동일비중)",
      {"strategy": [o.get("mean_per_exp_day_pct"), o.get("sharpe_per_exp_day")], "bh": [b["mean_pct"], b["sharpe"]]},
      (o.get("mean_per_exp_day_pct") or -9) >= b["mean_pct"] and sh >= b["sharpe"])
    res["criteria"] = crit
    fails = [x["criterion"] for x in crit if x["kills"] and not x["pass"]]
    res["verdict"] = "INCONCLUSIVE" if len(trades) < 30 else ("KILL" if fails else "SURVIVE")
    res["reasons"] = fails
    return res


def signals(doi: dict, pret: dict) -> tuple[dict, dict, dict]:
    """OI rule and price-only rule signal dates per coin, with train thresholds."""
    sig, ctrl, th = {}, {}, {}
    for c in COINS:
        tr_doi = [v for D, v in doi[c].items() if D < OOS0]
        tr_ret = [v for D, v in pret[c].items() if START <= D < OOS0]
        t_oi, t_px = quantile(tr_doi, Q), quantile(tr_ret, Q)
        th[c] = {"doi_q05": round(t_oi, 5), "ret_q05": round(t_px, 5), "train_n_doi": len(tr_doi), "train_n_ret": len(tr_ret)}
        sig[c] = sorted(D for D, v in doi[c].items() if D <= END and v <= t_oi and D in pret[c] and pret[c][D] < 0)
        ctrl[c] = sorted(D for D, v in pret[c].items() if START <= D <= END and v <= t_px)
    return sig, ctrl, th


def main():
    perp_raw = daily_bars("binance_perp_1d", only={f"{c}USDT" for c in COINS})
    perp = {c: perp_raw[f"{c}USDT"] for c in COINS}
    up_raw = daily_bars("upbit_krw_1d", key="market", only={f"KRW-{c}" for c in COINS})
    upbit = {c: up_raw[f"KRW-{c}"] for c in COINS}
    fund = {c: funding_by_day(f"{c}USDT") for c in COINS}
    pret = {c: {D: v[1] / v[0] - 1 for D, v in perp[c].items()} for c in COINS}
    doi, stale = load_doi("oi")
    sig, ctrl_sig, th = signals(doi, pret)

    res: dict = {"card": f"docs/research/cards/{SLUG}.md", "fees_per_side": FEE, "slip_per_side": SLIP,
                 "periods": {"train": [str(START), str(OOS0 - DAY)], "oos": [str(OOS0), str(END)]},
                 "thresholds_train": th, "stale_snapshots": stale,
                 "signal_counts": {c: {"train": sum(D < OOS0 for D in sig[c]), "oos": sum(D >= OOS0 for D in sig[c])} for c in COINS}}
    for venue, bars in (("upbit", upbit), ("perp", perp)):
        trades = run(sig, venue, bars, fund)
        ctrl = run(ctrl_sig, venue, bars, fund)
        res[venue] = evaluate(trades, ctrl, bars, venue, fund)
        res[venue]["trades"] = [{k: (round(v, 5) if isinstance(v, float) else v) for k, v in t.items()} for t in trades]
        assert all(doi[t["sym"]][t["date"]] <= th[t["sym"]]["doi_q05"] + 1e-12 and pret[t["sym"]][t["date"]] < 0
                   for t in trades), "every trade must satisfy both signal conditions"
        assert all(t["date"] >= START for t in trades)

    # info only: conservative pre-close OI (oi_pre ~23:55) with the same train-threshold procedure
    doi_pre, _ = load_doi("oi_pre")
    sp, _, thp = signals(doi_pre, pret)
    tp = run(sp, "upbit", upbit, fund)
    res["info_oi_pre_upbit"] = {"thresholds": thp, "oos_x2": stats([t for t in tp if t["date"] >= OOS0]),
                                "train_x2": stats([t for t in tp if t["date"] < OOS0])}
    res["verdict"] = res["upbit"]["verdict"]
    res["primary"] = "upbit"

    path = write_json(SLUG, res)
    print("thresholds", th)
    print("signals", res["signal_counts"])
    for venue in ("upbit", "perp"):
        r = res[venue]
        print(f"== {venue}", r["n_trades"])
        for k in ("full_base", "full_x2", "train_x2", "oos_base", "oos_x2", "full_h1_x2", "full_h2_x2", "oos_h1_x2",
                  "oos_h2_x2", "random_oos_x2", "oos_trades_per_year", "sma200_report_only", "price_only_control", "bh_oos"):
            print(k, r[k])
        for c in COINS:
            print(c, "oos", r[f"oos_{c}_x2"], "train", r[f"train_{c}_x2"])
        for x in r["criteria"]:
            print(x)
        print(r["verdict"], r["reasons"])
    print("oi_pre", res["info_oi_pre_upbit"])
    print("VERDICT", res["verdict"], path)


if __name__ == "__main__":
    main()
