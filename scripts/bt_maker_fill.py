"""T-035 maker-fill-rsi-ichi-5m-long: taker (A) vs maker trade-through fill (B) on the frozen RSI-Ichi 5m long.

Card: docs/research/cards/maker-fill-rsi-ichi-5m-long.md  Data: data/research/binance_perp_5m.csv
Run:  python scripts/bt_maker_fill.py
"""
from __future__ import annotations

import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bot.compute import _ichimoku, _rsi  # noqa: E402
from bt_cards_common import N_RANDOM, pct_rank, pf, rng, rows, summarize, write_json  # noqa: E402

SLUG = "maker-fill-rsi-ichi-5m-long"
RSI_THR, SL, TP, N_WAIT = 22.0, 0.005, 0.02, 1
COST = {
    "x0": dict(taker=0.0, maker=0.0, slip=0.0),
    "x1": dict(taker=0.0006, maker=0.0002, slip=0.0002),
    "x2": dict(taker=0.0012, maker=0.0004, slip=0.0004),
}
BAR = 300_000
FUNDING_MS = 8 * 3_600_000


def ms(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp() * 1000)


IS_WIN = (ms("2025-08-04"), ms("2026-08-05"))
OOS_START = ms("2020-01-01")


def in_oos(t: int) -> bool:
    return t >= OOS_START and not (IS_WIN[0] <= t < IS_WIN[1])


def in_is(t: int) -> bool:
    return IS_WIN[0] <= t < IS_WIN[1]


def load(sym: str) -> SimpleNamespace:
    bars = sorted(
        (int(r["open_time_ms"]), float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]))
        for r in rows("binance_perp_5m")
        if r["symbol"] == sym
    )
    T, o, h, l, c = (list(x) for x in zip(*bars))
    gaps = sum(1 for a, b in zip(T, T[1:]) if b - a != BAR)
    rsi = _rsi(c, {"period": 14})["rsi"]
    ichi = _ichimoku(SimpleNamespace(high=h, low=l, close=c), {})
    l1, l2 = ichi["Leading1"], ichi["Leading2"]
    n = len(c)
    below = [False] * n
    sig = []
    for i in range(1, n):
        if i >= 26 and l1[i - 26] is not None and l2[i - 26] is not None:
            below[i] = c[i] < l1[i - 26] and c[i] < l2[i - 26]
        if rsi[i - 1] is not None and rsi[i - 1] < RSI_THR and rsi[i] > RSI_THR:
            sig.append(i)
    return SimpleNamespace(sym=sym, T=T, o=o, h=h, l=l, c=c, n=n, below=below, sig=sig, gaps=gaps)


def sim_a(d, t: int, k_: dict):
    """Taker: buy next open, SL/TP/signal exits all taker. Returns trade dict or None (no data)."""
    if t + 1 >= d.n:
        return None
    slip = k_["slip"]
    e = d.o[t + 1] * (1 + slip)
    stop, tp = e * (1 - SL), e * (1 + TP)
    for k in range(t + 1, d.n):
        if d.l[k] <= stop:
            x, kind, xb = min(d.o[k], stop) * (1 - slip), "sl", k
        elif d.h[k] >= tp:
            x, kind, xb = tp * (1 - slip), "tp", k
        elif d.below[k] and k + 1 < d.n:
            x, kind, xb = d.o[k + 1] * (1 - slip), "sig", k + 1
        else:
            continue
        return dict(t=t, filled=True, eb=t + 1, xb=xb, kind=kind, ret=x / e - 1 - 2 * k_["taker"])
    return None


def sim_b(d, t: int, k_: dict):
    """Maker: limit at signal close, fills only on trade-through within N_WAIT bars; see card for exits."""
    if t + N_WAIT >= d.n:
        return None
    L = d.c[t]
    fb = next((k for k in range(t + 1, t + 1 + N_WAIT) if d.l[k] < L), None)
    if fb is None:
        return dict(t=t, filled=False, free=t + N_WAIT)
    slip, taker, maker = k_["slip"], k_["taker"], k_["maker"]
    stop, tp = L * (1 - SL), L * (1 + TP)
    pend = None  # (limit price, bar it was placed at close of)
    k = fb
    while k < d.n:
        if d.l[k] <= stop:
            amb = bool(pend and d.h[k] > pend[0])  # same bar also traded through the exit limit; SL-first is the card's conservative order
            x, fee, kind, xb = (stop if k == fb else min(d.o[k], stop)) * (1 - slip), taker, "sl_ambiguous" if amb else "sl", k
        elif pend and d.h[k] > pend[0]:
            x, fee, kind, xb = pend[0], maker, "sig_maker", k
        elif k > fb and d.h[k] > tp:
            x, fee, kind, xb = tp, maker, "tp", k
        elif pend and k - pend[1] >= N_WAIT:
            if k + 1 >= d.n:
                return None
            x, fee, kind, xb = d.o[k + 1] * (1 - slip), taker, "sig_taker_fallback", k + 1
        else:
            if pend is None and d.below[k]:
                pend = (d.c[k], k)
            k += 1
            continue
        return dict(t=t, filled=True, eb=fb, xb=xb, kind=kind, ret=x / L - 1 - maker - fee, free=xb)
    return None


def sim_toolkit(d, t: int):
    """Original toolkit fill (optimistic, fee-free): buy at signal close, signal exit at that bar's close."""
    e = d.c[t]
    stop, tp = e * (1 - SL), e * (1 + TP)
    for k in range(t + 1, d.n):
        if d.l[k] <= stop:
            return dict(t=t, filled=True, xb=k, ret=-SL)
        if d.h[k] >= tp:
            return dict(t=t, filled=True, xb=k, ret=TP)
        if d.below[k]:
            return dict(t=t, filled=True, xb=k, ret=d.c[k] / e - 1)
    return None


def run(d, model: str, cost: str, win) -> list[dict]:
    """Sequential, one position or pending order at a time. Returns all signal outcomes (filled or not)."""
    out, free = [], 0
    for t in d.sig:
        if t < free or not win(d.T[t]):
            continue
        if model == "A":
            r = sim_a(d, t, COST[cost])
        elif model == "B":
            r = sim_b(d, t, COST[cost])
        else:
            r = sim_toolkit(d, t)
        if r is None:
            break
        out.append(r)
        free = r.get("free", r.get("xb", t + 1))
    return out


def stats(res: list[dict]) -> dict:
    tr = [r for r in res if r["filled"]]
    s = summarize([r["ret"] for r in tr])
    if tr:
        s["sum_pct"] = round(sum(r["ret"] for r in tr) * 100, 2)
        s["signals"] = len(res)
        s["fill_rate_pct"] = round(len(tr) / len(res) * 100, 1)
        kinds: dict = {}
        for r in tr:
            k = r.get("kind", "toolkit")
            kinds[k] = kinds.get(k, 0) + 1
        s["exit_kinds"] = kinds
    return s


def halves_by_count(res):
    tr = [r for r in res if r["filled"]]
    m = len(tr) // 2
    return stats(tr[:m]), stats(tr[m:])


def funding_crossings(d, res) -> int:
    return sum(1 for r in res if r["filled"] and d.T[r["xb"]] // FUNDING_MS > d.T[r["eb"]] // FUNDING_MS)


def adverse_selection(d, res_b) -> dict:
    """Fee-free taker counterfactual for every B signal: filled vs unfilled."""
    filled, unfilled = [], []
    for r in res_b:
        cf = sim_a(d, r["t"], COST["x0"])
        if cf:
            (filled if r["filled"] else unfilled).append(cf["ret"])

    def m(x):
        return round(statistics.fmean(x) * 100, 4) if x else None

    diff = None
    if len(filled) > 1 and len(unfilled) > 1:
        se = (statistics.variance(filled) / len(filled) + statistics.variance(unfilled) / len(unfilled)) ** 0.5
        diff = round((statistics.fmean(filled) - statistics.fmean(unfilled)) / se, 2) if se else None
    return {
        "n_filled": len(filled),
        "n_unfilled": len(unfilled),
        "cf_mean_pct_filled": m(filled),
        "cf_mean_pct_unfilled": m(unfilled),
        "cf_pf_filled": pf(filled),
        "cf_pf_unfilled": pf(unfilled),
        "welch_t_filled_minus_unfilled": diff,
    }


def random_entries(d, res_b) -> dict:
    """Same count of B signals, each redrawn from OOS bars with the same cloud state; same B sim at x2."""
    pool = {True: [], False: []}
    for i in range(60, d.n - 3):
        if in_oos(d.T[i]):
            pool[d.below[i]].append(i)
    actual = [r["ret"] for r in res_b if r["filled"]]
    actual_mean = statistics.fmean(actual)
    want = [d.below[r["t"]] for r in res_b]
    g = rng()
    dist = []
    for _ in range(N_RANDOM):
        rets = []
        for b in want:
            r = sim_b(d, g.choice(pool[b]), COST["x2"])
            if r and r["filled"]:
                rets.append(r["ret"])
        dist.append(statistics.fmean(rets) if rets else 0.0)
    q = sorted(dist)
    return {
        "actual_mean_pct": round(actual_mean * 100, 4),
        "random_p50_pct": round(q[len(q) // 2] * 100, 4),
        "random_p99_pct": round(q[int(len(q) * 0.99) - 1] * 100, 4),
        "percentile": pct_rank(actual_mean, dist),
        "signals_below_cloud_share_pct": round(sum(want) / len(want) * 100, 1),
    }


def bh(d, win) -> dict:
    idx = [i for i in range(d.n) if win(d.T[i])]
    segs, cur = [], [idx[0]]
    for a, b in zip(idx, idx[1:]):
        if b != a + 1:
            segs.append(cur)
            cur = [b]
        else:
            cur.append(b)
    segs.append(cur)
    return {
        f"{datetime.fromtimestamp(d.T[s[0]] / 1000, timezone.utc):%Y-%m-%d}~"
        f"{datetime.fromtimestamp(d.T[s[-1]] / 1000, timezone.utc):%Y-%m-%d}": round((d.c[s[-1]] / d.o[s[0]] - 1) * 100, 2)
        for s in segs
    }


def _selfcheck() -> None:
    def d(lows, highs, below, closes=None, opens=None):
        n = len(lows)
        return SimpleNamespace(n=n, l=lows, h=highs, below=below, c=closes or [100.0] * n, o=opens or [100.0] * n)

    x0 = COST["x0"]
    assert not sim_b(d([100, 100, 100], [101] * 3, [False] * 3), 0, x0)["filled"]  # touch is not a fill
    r = sim_b(d([100, 99.9, 100], [100, 100.2, 100.15], [False, True, False], [100, 100.1, 100]), 0, x0)
    assert r["kind"] == "sig_maker" and abs(r["ret"] - 0.001) < 1e-12
    r = sim_b(d([100, 99.9, 100, 100], [100, 100.2, 100.1, 100], [False, True, False, False],
                [100, 100.1, 100, 100], [100, 100, 100, 99.8]), 0, x0)
    assert r["kind"] == "sig_taker_fallback" and abs(r["ret"] + 0.002) < 1e-12  # touch-only exit -> taker next open
    r = sim_b(d([100, 99.4, 100], [100, 100, 100], [False] * 3), 0, x0)
    assert r["kind"] == "sl" and abs(r["ret"] + SL) < 1e-12


def main() -> None:
    _selfcheck()
    out: dict = {"card": f"docs/research/cards/{SLUG}.md", "n_wait": N_WAIT, "cost": COST}
    btc = load("BTCUSDT")
    eth = load("ETHUSDT")
    for d in (btc, eth):
        out[f"data_{d.sym}"] = {
            "bars": d.n,
            "first": datetime.fromtimestamp(d.T[0] / 1000, timezone.utc).isoformat(),
            "last": datetime.fromtimestamp(d.T[-1] / 1000, timezone.utc).isoformat(),
            "gaps": d.gaps,
            "signals_all": len(d.sig),
        }
    print("data", out["data_BTCUSDT"], out["data_ETHUSDT"], flush=True)

    out["is_replication_toolkit_fee0"] = {
        "BTC_IS": stats(run(btc, "T", "x0", in_is)),
        "BTC_OOS": stats(run(btc, "T", "x0", in_oos)),
    }
    print("toolkit-style fee0", out["is_replication_toolkit_fee0"], flush=True)

    res = {}
    for model in ("A", "B"):
        for cost in ("x0", "x1", "x2"):
            res[(model, cost)] = run(btc, model, cost, in_oos)
            out[f"BTC_OOS_{model}_{cost}"] = stats(res[(model, cost)])
            print(model, cost, out[f"BTC_OOS_{model}_{cost}"], flush=True)
        out[f"BTC_IS_{model}_x1"] = stats(run(btc, model, "x1", in_is))

    b2 = res[("B", "x2")]
    h1, h2 = halves_by_count(b2)
    out["BTC_OOS_B_x2_halves"] = {"h1": h1, "h2": h2}
    out["exit_maker_fill_rate_pct"] = (
        lambda k: round(k.get("sig_maker", 0) / max(1, k.get("sig_maker", 0) + k.get("sig_taker_fallback", 0)) * 100, 1)
    )(out["BTC_OOS_B_x2"].get("exit_kinds", {}))
    out["funding_crossings_B_x2"] = funding_crossings(btc, b2)
    out["adverse_selection_BTC"] = adverse_selection(btc, b2)
    print("adverse", out["adverse_selection_BTC"], flush=True)

    eth_b2 = run(eth, "B", "x2", in_oos)
    out["ETH_OOS_B_x2"] = stats(eth_b2)
    out["ETH_OOS_A_x2"] = stats(run(eth, "A", "x2", in_oos))
    out["ETH_OOS_B_x0"] = stats(run(eth, "B", "x0", in_oos))
    out["adverse_selection_ETH"] = adverse_selection(eth, eth_b2)
    out["bh_BTC_OOS_pct"] = bh(btc, in_oos)

    out["random_BTC_B_x2"] = random_entries(btc, b2)
    print("random", out["random_BTC_B_x2"], flush=True)

    sB, sA = out["BTC_OOS_B_x2"], out["BTC_OOS_A_x2"]
    rnd = out["random_BTC_B_x2"]
    crit = {
        "1_B_pf_x2_ge_1.1": (sB.get("pf") or 0) >= 1.1,
        "2_B_trades_ge_150": sB.get("n", 0) >= 150,
        "3_random_ge_99pct": rnd["percentile"] >= 99,
        "4_B_beats_A_pf_and_sum": (sB.get("pf") or 0) > (sA.get("pf") or 0) and sB.get("sum_pct", -1e9) > sA.get("sum_pct", -1e9),
        "5_halves_pf_ge_1.0": all((x.get("pf") or 0) >= 1.0 for x in (h1, h2)),
        "6_eth_pf_x2_ge_1.0": (out["ETH_OOS_B_x2"].get("pf") or 0) >= 1.0,
    }
    out["criteria"] = crit
    hard = [k for k in crit if k != "2_B_trades_ge_150"]
    if not all(crit[k] for k in hard):
        verdict = "KILL"
    elif not crit["2_B_trades_ge_150"]:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "SURVIVE"
    out["verdict"] = verdict
    p = write_json(SLUG, out)
    print("criteria", crit, "\nverdict", verdict, "\nwrote", p, flush=True)


if __name__ == "__main__":
    main()
