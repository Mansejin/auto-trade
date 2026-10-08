#!/usr/bin/env python3
"""Red-team the SMA200 daily filter: close[i] > SMA200(close..i) -> hold over day i+1 (open[i+1] -> open[i+2]), else cash.

Run sma200_data.py first (caches _data/). Cash earns 0. Fee is charged per side on |dw| at the open.
Writes sma200_redteam_out.json.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sma200_data import load  # noqa: E402

BASE_FEE = 0.0005  # Upbit taker per side
FEES = {"x1 0.05%": BASE_FEE, "x2 0.10%": 2 * BASE_FEE, "x4 0.20%": 4 * BASE_FEE}
N_RANDOM = 1000
SEED = 20261008


def signal(closes: list[float], n: int) -> list[float | None]:
    out, s = [None] * len(closes), 0.0
    for i, c in enumerate(closes):
        s += c
        if i >= n:
            s -= closes[i - n]
        if i >= n - 1:
            out[i] = 1.0 if c > s / n else 0.0
    return out


def build(rows: list, n: int = 200, lag: int = 1):
    """Returns per held-day arrays (date, r_open_to_open, w). w for day j uses signal at close j-lag."""
    dates = [r[0] for r in rows]
    opens = [r[1] for r in rows]
    sig = signal([r[2] for r in rows], n)
    d, r, w = [], [], []
    for j in range(lag, len(rows) - 1):
        s = sig[j - lag]
        if s is None:
            continue
        d.append(dates[j])
        r.append(opens[j + 1] / opens[j] - 1)
        w.append(s)
    return d, r, w


def stats(r: list[float], w: list[float], fee: float, w0: float = 0.0) -> dict:
    eq, peak, mdd, prev, rets, sw, fee_drag = 1.0, 1.0, 0.0, w0, [], 0, 0.0
    for ri, wi in zip(r, w):
        f = fee * abs(wi - prev)
        sw += wi != prev
        fee_drag += f
        x = (1 - f) * (1 + wi * ri) - 1
        rets.append(x)
        eq *= 1 + x
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
        prev = wi
    n = len(rets)
    m = sum(rets) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in rets) / (n - 1))
    yrs = n / 365
    return {
        "ret_pct": round((eq - 1) * 100, 1),
        "cagr_pct": round((eq ** (1 / yrs) - 1) * 100, 1) if eq > 0 else -100.0,
        "mdd_pct": round(mdd * 100, 1),
        "sharpe": round(m / sd * math.sqrt(365), 2) if sd else 0.0,
        "calmar": round(((eq ** (1 / yrs) - 1) / -mdd), 2) if mdd < 0 and eq > 0 else None,
        "exposure_pct": round(sum(w) / n * 100, 1),
        "switches": sw,
        "fee_drag_pct": round(fee_drag * 100, 2),
        "days": n,
    }


def runs(w: list[float]) -> list[tuple[float, int]]:
    out = []
    for x in w:
        if out and out[-1][0] == x:
            out[-1] = (x, out[-1][1] + 1)
        else:
            out.append((x, 1))
    return out


def composition(total: int, k: int, rng: random.Random) -> list[int]:
    cuts = sorted(rng.sample(range(1, total), k - 1)) if k > 1 else []
    b = [0, *cuts, total]
    return [b[i + 1] - b[i] for i in range(k)]


def random_baseline(r, w, fee):
    """Random on/off schedules with the same start state, number of on/off runs (=> same switches) and on-days."""
    rs = runs(w)
    on_runs = [L for x, L in rs if x == 1.0]
    off_runs = [L for x, L in rs if x == 0.0]
    rng = random.Random(SEED)
    res = []
    for _ in range(N_RANDOM):
        on = composition(sum(on_runs), len(on_runs), rng)
        off = composition(sum(off_runs), len(off_runs), rng)
        rng.shuffle(on), rng.shuffle(off)
        seq, oi, fi = [], iter(on), iter(off)
        for x, _L in rs:
            seq += [x] * (next(oi) if x == 1.0 else next(fi))
        res.append(stats(r, seq, fee))
    real = stats(r, w, fee)

    def pct(key, higher_better=True):
        v = real[key]
        xs = [s[key] for s in res]
        return round(100 * sum((x < v) if higher_better else (x > v) for x in xs) / len(xs), 1)

    med = lambda k: sorted(s[k] for s in res)[len(res) // 2]  # noqa: E731
    return {
        "real": real,
        "random_median": {k: med(k) for k in ("ret_pct", "sharpe", "mdd_pct", "calmar")},
        "percentile_ret": pct("ret_pct"),
        "percentile_sharpe": pct("sharpe"),
        "percentile_mdd_(share of randoms with deeper MDD)": pct("mdd_pct"),
    }


def exposure_matched(r, w, fee):
    e = sum(w) / len(w)
    const = stats(r, [e] * len(r), fee, w0=e)  # daily-rebalanced constant weight (rebalance cost ignored, tiny)
    eq_btc, cash, peak, mdd = e, 1 - e, 1.0, 0.0  # static: buy e once, never rebalance
    for ri in r:
        eq_btc *= 1 + ri
        v = eq_btc + cash
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    return {
        "exposure": round(e, 3),
        "const_weight_daily_rebal": const,
        "static_buy_e_hold": {"ret_pct": round((eq_btc + cash - 1) * 100, 1), "mdd_pct": round(mdd * 100, 1)},
    }


def per_year(d, r, w, fee):
    out = {}
    years = sorted({x[:4] for x in d})
    for y in years:
        idx = [i for i, x in enumerate(d) if x[:4] == y]
        if len(idx) < 60:
            continue
        rr = [r[i] for i in idx]
        ww = [w[i] for i in idx]
        w0 = w[idx[0] - 1] if idx[0] > 0 else 0.0
        s = stats(rr, ww, fee, w0=w0)
        b = stats(rr, [1.0] * len(rr), 0.0, w0=1.0)
        out[y] = {
            "days": len(idx), "strat_ret": s["ret_pct"], "bh_ret": b["ret_pct"],
            "strat_mdd": s["mdd_pct"], "bh_mdd": b["mdd_pct"], "exposure": s["exposure_pct"],
            "switches": s["switches"], "fee_pct": s["fee_drag_pct"],
        }
    return out


def round_trips(d, r, w, fee):
    """Each holding run: entry date, days, net return incl. both fees."""
    trips, i = [], 0
    while i < len(w):
        if w[i] == 1.0:
            j, g = i, 1.0
            while j < len(w) and w[j] == 1.0:
                g *= 1 + r[j]
                j += 1
            trips.append({"entry": d[i], "days": j - i, "ret_pct": round(((1 - fee) ** 2 * g - 1) * 100, 2)})
            i = j
        else:
            i += 1
    return trips


def whipsaw(trips, short=20):
    losers = [t for t in trips if t["ret_pct"] < 0]
    by_year = {}
    for t in trips:
        y = by_year.setdefault(t["entry"][:4], {"trips": 0, "losers": 0, "short_le_%dd" % short: 0, "loss_compound_pct": 1.0})
        y["trips"] += 1
        if t["days"] <= short:
            y["short_le_%dd" % short] += 1
        if t["ret_pct"] < 0:
            y["losers"] += 1
            y["loss_compound_pct"] *= 1 + t["ret_pct"] / 100
    for y in by_year.values():
        y["loss_compound_pct"] = round((y["loss_compound_pct"] - 1) * 100, 1)
    srt = sorted(trips, key=lambda t: -t["ret_pct"])
    comp = lambda ts: round((math.prod(1 + t["ret_pct"] / 100 for t in ts) - 1) * 100, 1)  # noqa: E731
    return {
        "n_trips": len(trips), "n_losers": len(losers),
        "win_rate_pct": round(100 * (1 - len(losers) / len(trips)), 1) if trips else None,
        "median_loser_pct": sorted(t["ret_pct"] for t in losers)[len(losers) // 2] if losers else None,
        "top5": srt[:5],
        "all_trips_compound_pct": comp(trips),
        "without_top1_pct": comp(srt[1:]),
        "without_top5_pct": comp(srt[5:]),
        "by_entry_year": by_year,
    }


def window(d, r, w, a, b):
    idx = [i for i, x in enumerate(d) if a <= x <= b]
    w0 = w[idx[0] - 1] if idx and idx[0] > 0 else 0.0
    return [d[i] for i in idx], [r[i] for i in idx], [w[i] for i in idx], w0


def main() -> None:
    out: dict = {"fee_base": BASE_FEE}
    btc = load("upbit_KRW-BTC")
    d, r, w = build(btc)
    out["primary"] = {"series": "upbit KRW-BTC", "from": d[0], "to": d[-1]}

    # 1. fees + execution lag stress
    out["fees"] = {k: stats(r, w, f) for k, f in FEES.items()}
    out["fees"]["B&H"] = stats(r, [1.0] * len(r), BASE_FEE, w0=0.0)
    d2, r2, w2 = build(btc, lag=2)
    out["exec_extra_1day_delay_x1"] = stats(r2, w2, BASE_FEE)
    out["exec_extra_1day_delay_note"] = f"lag-2 series starts {d2[0]} (vs {d[0]})"

    # 2. random baseline
    out["random"] = {k: random_baseline(r, w, f) for k, f in (("x1", BASE_FEE), ("x2", 2 * BASE_FEE))}
    for tag, (a, b) in {"IS 2021-07-27..2026-07-26": ("2021-07-27", "2026-07-26"), "OOS 2018-04-12..2021-07-24": ("2018-04-12", "2021-07-24")}.items():
        dd, rr, ww, _ = window(d, r, w, a, b)
        out["random"][tag] = random_baseline(rr, ww, BASE_FEE)

    # 3. transfer
    tr = {}
    for name in ("upbit_KRW-BTC", "upbit_KRW-ETH", "upbit_KRW-XRP", "binance_BTCUSDT", "binance_ETHUSDT", "binance_XRPUSDT", "bitstamp_BTCUSD"):
        rows = load(name)
        dd, rr, ww = build(rows)
        segs = {"full": (dd[0], dd[-1])}
        if name == "bitstamp_BTCUSD":
            segs = {"pre2018 (..2017-12-31)": (dd[0], "2017-12-31"), "2018+": ("2018-01-01", dd[-1]), "full": (dd[0], dd[-1])}
        for sname, (a, b) in segs.items():
            d_, r_, w_, w0 = window(dd, rr, ww, a, b)
            key = f"{name} {sname}"
            tr[key] = {
                "from": d_[0], "to": d_[-1],
                "sma200_x1": stats(r_, w_, BASE_FEE, w0=0.0),
                "sma200_x2": stats(r_, w_, 2 * BASE_FEE, w0=0.0),
                "bh": stats(r_, [1.0] * len(r_), BASE_FEE, w0=0.0),
                "exposure_matched": exposure_matched(r_, w_, BASE_FEE),
                "random_pct": {kk: v for kk, v in random_baseline(r_, w_, BASE_FEE).items() if kk.startswith("percentile")},
            }
    out["transfer"] = tr

    # same BTC rule, same window, three venues (KRW premium / FX / venue-path sensitivity)
    a, b = d[0], d[-1]
    venue = {}
    for name in ("upbit_KRW-BTC", "binance_BTCUSDT", "bitstamp_BTCUSD"):
        dd, rr, ww = build(load(name))
        d_, r_, w_, _ = window(dd, rr, ww, a, b)
        venue[name] = {"sma200": stats(r_, w_, BASE_FEE), "bh": stats(r_, [1.0] * len(r_), BASE_FEE)}
    out["venue_common_window"] = {"from": a, "to": b, **venue}

    # 4. regimes / years / whipsaw
    out["per_year"] = per_year(d, r, w, BASE_FEE)
    bs = load("bitstamp_BTCUSD")
    bd, br, bw = build(bs)
    out["per_year_bitstamp"] = per_year(bd, br, bw, BASE_FEE)
    out["whipsaw_upbit"] = whipsaw(round_trips(d, r, w, BASE_FEE))
    out["whipsaw_bitstamp"] = whipsaw(round_trips(bd, br, bw, BASE_FEE))

    # 5. neighbours (no selection; plateau check). Common start so windows match.
    neigh = {}
    for src, rows in (("upbit_KRW-BTC", btc), ("bitstamp_BTCUSD", bs), ("upbit_KRW-ETH", load("upbit_KRW-ETH")), ("upbit_KRW-XRP", load("upbit_KRW-XRP"))):
        common = build(rows, 300)[0][0]
        neigh[src] = {"from": common}
        for n in (100, 150, 175, 200, 225, 250, 300):
            dd, rr, ww = build(rows, n)
            d_, r_, w_, _ = window(dd, rr, ww, common, dd[-1])
            neigh[src][f"SMA{n}"] = {kk: v for kk, v in stats(r_, w_, BASE_FEE).items() if kk in ("ret_pct", "cagr_pct", "mdd_pct", "sharpe", "switches", "exposure_pct")}
        d_, r_, _, _ = window(dd, rr, ww, common, dd[-1])
        neigh[src]["B&H"] = {kk: v for kk, v in stats(r_, [1.0] * len(r_), BASE_FEE).items() if kk in ("ret_pct", "cagr_pct", "mdd_pct", "sharpe")}
    out["neighbours"] = neigh

    # 6. exposure-matched B&H on primary
    out["exposure_matched_primary"] = exposure_matched(r, w, BASE_FEE)
    out["sma200_primary_x1"] = out["fees"]["x1 0.05%"]

    txt = json.dumps(out, indent=1, ensure_ascii=False)
    (HERE / "sma200_redteam_out.json").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
