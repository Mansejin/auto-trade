#!/usr/bin/env python3
"""Card xs-funding-crowding-weekly (frozen 2026-10-08, board T-028/T-039), encoded as-is. No tuning.

Rule: every Monday 00:00 UTC, universe = top 30 alts by trailing 30d perp quote volume (listed >= 30 days, BTC/ETH/stables
excluded). Rank by trailing 7d funding: highest 5 short, lowest 5 long, equal notional, hold 7 days (open t -> open t+7).
Delisted while held: short leg price PnL 0, long leg -50% (card). PnL = price + funding - costs.

Implementation decisions fixed before results (T-039, lead):
 1. coins only: underlying_type COIN or blank; excluded BTCUSDT, ETHUSDT, USDCUSDT and gold-pegged PAXGUSDT, XAUTUSDT.
 2. start = first Monday (from 2020-06-01) with >= 30 eligible symbols after dedupe; earlier weeks skipped.
 3. listed >= 30 days = 30 consecutive tradable days before t (streak restarts after any tradable=0/missing day);
    returns never span a tradable=0 gap.
 4. 1000XXX / 1000000XXX / 1MXXX vs XXX: same base name in a week -> keep the higher trailing-volume one (before top-30).
 5. held symbol stops being tradable before exit open -> exit at last tradable close (card delist rule applied to price).
 6. random null: same rebalance dates, random 5L/5S from that week's universe (date-clustered), 1,000 runs, pre-cost basis;
    thresholds 95 (card) and 99 (board: ~175 strategies tried). Pooled independent-leg null is info only.
Further encoding details (also fixed before results):
 - signal = sum of tradable funding settlements with time in [t-L days, t) (L=7; neighbours 3, 14) -> daily-equivalent,
   so 1h/4h/8h interval symbols are comparable. Ties broken by symbol.
 - holding funding = settlements in (t, exit], fixed quantity: rate * open(settlement day) / entry open. Long pays, short receives.
 - 1x short loses 100% (funding ignored) if the daily high reaches 2x entry during the hold.
 - capital split 50/50 between legs, 1x each: weekly return = (mean long leg + mean short leg) / 2.
 - costs per side: x2 = fee 0.12% + slip 0.20% = 0.32%; base = 0.06% + 0.20% = 0.26%. Charged on turnover only (leg entered
   / exited); unchanged legs pay nothing (weight drift ignored). Full-turnover variant reported.
 - split by rebalance date: train < 2023-07-01 <= OOS.

Run: uv run --no-project --with pandas python -u scripts/bt_xs_funding_crowding.py
 -> reports/research-cards/xs-funding-crowding-weekly.json
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from bt_cards_common import DATA, N_RANDOM, SEED, halves, pct_rank, pf, sharpe, summarize, write_json

SLUG = "xs-funding-crowding-weekly"
EXCLUDE = {"BTCUSDT", "ETHUSDT", "USDCUSDT", "PAXGUSDT", "XAUTUSDT"}
SCAN0 = pd.Timestamp("2020-06-01")
OOS0 = pd.Timestamp("2023-07-01")
UNIV_N, MIN_DAYS, VOL_DAYS, LEGS, HOLD, MOM_DAYS = 30, 30, 30, 5, 7, 28
LOOKBACKS = (7, 3, 14)
COST = {"gross": 0.0, "base": 0.0026, "x2": 0.0032}
DAY_MS = 86_400_000


def base_name(s: str) -> str:
    b = s[:-4]
    for p in ("1000000", "1000", "1M"):
        if b.startswith(p) and len(b) > len(p):
            return b[len(p):]
    return b


def wsum(times, cum, a, b, side):
    """sum over settlements in [a, b) (side='left') or (a, b] (side='right')."""
    return cum[np.searchsorted(times, b, side)] - cum[np.searchsorted(times, a, side)]


def _selfcheck():
    assert base_name("1000PEPEUSDT") == "PEPE" and base_name("1000000BOBUSDT") == "BOB"
    assert base_name("1MBABYDOGEUSDT") == "BABYDOGE" and base_name("1INCHUSDT") == "1INCH"
    t = np.array([0, 10, 20]); c = np.array([0, 1, 3, 6])
    assert wsum(t, c, 0, 20, "left") == 3 and wsum(t, c, 0, 20, "right") == 5


def load():
    u = pd.read_csv(DATA / "binance_um_universe.csv", keep_default_na=False)
    coins = set(u.loc[u.underlying_type.isin(["COIN", ""]), "symbol"]) - EXCLUDE
    k = pd.read_csv(DATA / "binance_um_all_1d.csv", usecols=["symbol", "date_utc", "open", "high", "close", "quote_volume", "tradable"])
    k = k[k.symbol.isin(coins | {"BTCUSDT"})]
    k["date_utc"] = pd.to_datetime(k.date_utc)
    days = pd.date_range(k.date_utc.min(), k.date_utc.max(), freq="D")
    W = {c: k.pivot(index="date_utc", columns="symbol", values=c).reindex(days) for c in ["open", "high", "close", "quote_volume", "tradable"]}
    syms = W["open"].columns
    W = {c: v[syms] for c, v in W.items()}
    W["tradable"] = W["tradable"].fillna(0).astype(np.int8)
    print(f"daily: {len(k):,} rows, {len(syms)} symbols, {days[0].date()}..{days[-1].date()}", flush=True)

    f = pd.read_csv(DATA / "funding_um_all.csv", usecols=["symbol", "funding_time_ms", "funding_rate", "tradable"])
    n_all = len(f)
    f = f[(f.tradable == 1) & f.symbol.isin(coins)].sort_values(["symbol", "funding_time_ms"])
    day0 = days[0].value // 1_000_000
    di = ((f.funding_time_ms.values - day0) // DAY_MS).clip(0, len(days) - 1)
    op = np.nan_to_num(W["open"].values[di, syms.get_indexer(f.symbol)])
    f = f.assign(ro=f.funding_rate.values * op)
    fund = {}
    for s, g in f.groupby("symbol", sort=False):
        fund[s] = (g.funding_time_ms.values, np.concatenate([[0.0], g.funding_rate.cumsum().values]),
                   np.concatenate([[0.0], g.ro.cumsum().values]))
    print(f"funding: {n_all:,} rows, tradable coin rows {len(f):,}, symbols {len(fund)}", flush=True)
    return coins, days, W, fund, day0


def main():
    _selfcheck()
    coins, days, W, fund, day0 = load()
    syms = list(W["open"].columns)
    O, H, C = W["open"].values, W["high"].values, W["close"].values
    T = W["tradable"].values
    Tdf = W["tradable"]
    c = Tdf.astype(np.int32).cumsum()
    streak = (c - c.where(Tdf == 0).ffill().fillna(0)).values
    vol30 = (W["quote_volume"].fillna(0) * Tdf).shift(1).rolling(VOL_DAYS).sum().values
    alt = np.array([s in coins for s in syms])
    bases = [base_name(s) for s in syms]
    dms = lambda i: day0 + i * DAY_MS

    mondays = [i for i, dd in enumerate(days) if dd.weekday() == 0 and dd >= SCAN0 and i + HOLD < len(days)]
    weeks, univ, skipped, dedup_drops, legs = [], [], [], [], {}
    for i in mondays:
        el = np.where(alt & (T[i] == 1) & (streak[i - 1] >= MIN_DAYS) & np.isfinite(vol30[i]))[0]
        el = el[np.argsort(-vol30[i, el], kind="stable")]
        seen, keep = {}, []
        for j in el:
            b = bases[j]
            if b in seen:
                dedup_drops.append((str(days[i].date()), syms[seen[b]], syms[j]))
                continue
            seen[b] = j
            keep.append(j)
        if not weeks and len(keep) < UNIV_N:
            skipped.append((str(days[i].date()), len(keep)))
            continue
        k = len(weeks)
        top = keep[:UNIV_N]
        row = []
        for j in top:
            s = syms[j]
            if s not in fund:
                continue
            ft, fr, fro = fund[s]
            t0 = dms(i)
            sig = {L: wsum(ft, fr, t0 - L * DAY_MS, t0, "left") / L for L in LOOKBACKS}
            if np.searchsorted(ft, t0, "left") - np.searchsorted(ft, t0 - 7 * DAY_MS, "left") == 0:
                continue
            P0 = O[i, j]
            win = T[i:i + HOLD, j]
            if win.all() and T[i + HOLD, j]:
                last, px, early = i + HOLD - 1, O[i + HOLD, j], False
            else:
                n = int(np.argmin(win)) if not win.all() else HOLD
                last, px, early = i + n - 1, C[i + n - 1, j], True
            t1 = dms(last + 1)
            F = wsum(ft, fro, t0, t1, "right") / P0
            ra = px / P0 - 1
            liq = bool(np.nanmax(H[i:last + 1, j]) >= 2 * P0)
            g = {"sym": s, "sig": sig, "mom": P0 / O[i - MOM_DAYS, j] - 1, "early": early, "liq": liq, "ra": ra, "F": F,
                 "lp": -0.5 if early else ra, "lf": -F,
                 "sp": -1.0 if liq else (0.0 if early else -ra), "sf": 0.0 if liq else F,
                 "lp_act": ra, "sp_act": -1.0 if liq else -ra}
            g["sf"] = max(g["sf"], -1.0 - g["sp"])
            legs[(k, s)] = g
            row.append(s)
        assert len(row) >= 2 * LEGS, (days[i], len(row))
        weeks.append(i)
        univ.append(row)
    K = len(weeks)
    wdates = [days[i] for i in weeks]
    oos_mask = np.array([d >= OOS0 for d in wdates])
    print(f"weeks {K} ({wdates[0].date()}..{wdates[-1].date()}), skipped {len(skipped)}, OOS {oos_mask.sum()}, "
          f"universe size min {min(map(len, univ))}", flush=True)

    def sel_by(key):
        """(longs, shorts) per week: lowest key long, highest key short."""
        out = []
        for k in range(K):
            r = sorted(univ[k], key=lambda s: (key(legs[(k, s)]), s))
            out.append((set(r[:LEGS]), set(r[-LEGS:])))
        return out

    def run(sel, cost, delist="card", full=False):
        rec = []
        for k in range(K):
            L, S = sel[k]
            pL, pS = sel[k - 1] if k else (set(), set())
            nL, nS = sel[k + 1] if k + 1 < K else (set(), set())
            out = {}
            for side, cur, prev, nxt in (("L", L, pL, nL), ("S", S, pS, nS)):
                p = f = cc = 0.0
                for s in cur:
                    g = legs[(k, s)]
                    ent = full or s not in prev or legs[(k - 1, s)]["early"]
                    ext = full or s not in nxt or g["early"]
                    if side == "L":
                        p += g["lp"] if delist == "card" else g["lp_act"]
                        f += g["lf"]
                    else:
                        p += g["sp"] if delist == "card" else g["sp_act"]
                        f += g["sf"]
                    cc += cost * (ent + ext)
                n = len(cur)
                out[side + "p"], out[side + "f"], out[side + "c"] = p / n, f / n, cc / n
            out["ret"] = (out["Lp"] + out["Lf"] - out["Lc"] + out["Sp"] + out["Sf"] - out["Sc"]) / 2
            rec.append(out)
        return pd.DataFrame(rec, index=pd.DatetimeIndex(wdates))

    def st(r):
        r = list(r)
        s = summarize(r)
        if r:
            s["mean_pct"] = round(float(np.mean(r)) * 100, 4)
            s["median_pct"] = round(float(np.median(r)) * 100, 4)
            s["sharpe_ann"] = sharpe(r, 52)
            s["sum_pct"] = round(sum(r) * 100, 2)
        return s

    sel = {L: sel_by(lambda g, L=L: g["sig"][L]) for L in LOOKBACKS}
    main_sel = sel[7]
    mom_sel = sel_by(lambda g: g["mom"])  # anti-momentum: low 28d return long, high short
    runs = {c: run(main_sel, v) for c, v in COST.items()}
    x2 = runs["x2"]
    oos_idx = x2.index >= OOS0
    tr, oo = x2[~oos_idx], x2[oos_idx]
    h1, h2 = halves(list(oo.index), lambda x: x)
    res: dict = {
        "card": f"docs/research/cards/{SLUG}.md", "board": "T-039",
        "decisions": __doc__.split("Implementation decisions fixed before results (T-039, lead):")[1].split("Run:")[0].strip(),
        "start_week": str(wdates[0].date()), "end_week": str(wdates[-1].date()), "n_weeks": K,
        "n_train": int((~oos_idx).sum()), "n_oos": int(oos_idx.sum()),
        "skipped_weeks_lt30": skipped, "dedupe_drops": dedup_drops,
        "universe_size_min_max": [min(map(len, univ)), max(map(len, univ))],
        "eligible_symbols_ever": len({s for r in univ for s in r}),
    }
    for c, df in runs.items():
        res[f"stats_{c}"] = {"full": st(df.ret), "train": st(df.ret[~oos_idx]), "oos": st(df.ret[oos_idx]),
                             "oos_h1": st(df.ret[df.index.isin(h1)]), "oos_h2": st(df.ret[df.index.isin(h2)])}
    full_to = run(main_sel, COST["x2"], full=True)
    res["oos_x2_full_turnover"] = st(full_to.ret[oos_idx])
    res["oos_x2_delist_actual_close"] = st(run(main_sel, COST["x2"], delist="actual").ret[oos_idx])

    # held legs: early exits / liquidations / turnover
    held = [(k, s, side) for k in range(K) for side, ss in zip("LS", main_sel[k]) for s in ss]
    res["held_legs"] = {"n": len(held), "early_exit": [f"{wdates[k].date()} {s} {side}" for k, s, side in held if legs[(k, s)]["early"]],
                        "liquidated": [f"{wdates[k].date()} {s} {side}" for k, s, side in held if side == "S" and legs[(k, s)]["liq"]]}
    chg = [len(main_sel[k][0] - main_sel[k - 1][0]) + len(main_sel[k][1] - main_sel[k - 1][1]) for k in range(1, K)]
    res["turnover_new_legs_per_week_mean"] = round(float(np.mean(chg)), 2)

    # leg breakdown (per-leg means; portfolio contribution = /2)
    def legs_br(df):
        m = df.mean()
        return {"long_price_pct": round(m.Lp * 100, 4), "long_funding_pct": round(m.Lf * 100, 4), "long_cost_pct": round(m.Lc * 100, 4),
                "long_net_pct": round((m.Lp + m.Lf - m.Lc) * 100, 4),
                "short_price_pct": round(m.Sp * 100, 4), "short_funding_pct": round(m.Sf * 100, 4), "short_cost_pct": round(m.Sc * 100, 4),
                "short_net_pct": round((m.Sp + m.Sf - m.Sc) * 100, 4),
                "portfolio_price_pct": round((m.Lp + m.Sp) / 2 * 100, 4), "portfolio_funding_pct": round((m.Lf + m.Sf) / 2 * 100, 4),
                "portfolio_cost_pct": round((m.Lc + m.Sc) / 2 * 100, 4)}
    res["legs_x2"] = {"full": legs_br(x2), "train": legs_br(tr), "oos": legs_br(oo)}
    res["by_year_x2"] = {str(y): st(g.ret) for y, g in x2.groupby(x2.index.year)}
    srt = oo.ret.sort_values(ascending=False)
    res["oos_top3_weeks"] = {"weeks": [{"t": str(t.date()), "x2_pct": round(v * 100, 3)} for t, v in srt[:3].items()],
                             "share_of_sum": round(float(srt[:3].sum() / srt.sum()), 3) if srt.sum() else None,
                             "drop_top3": st(srt[3:]),
                             "bottom3": [{"t": str(t.date()), "x2_pct": round(v * 100, 3)} for t, v in srt[-3:].items()]}

    # anti-momentum + neighbours
    mom = run(mom_sel, COST["x2"])
    res["anti_momentum_x2"] = {"full": st(mom.ret), "train": st(mom.ret[~oos_idx]), "oos": st(mom.ret[oos_idx]),
                               "oos_weekly_corr_with_card": round(float(np.corrcoef(mom.ret[oos_idx], oo.ret)[0, 1]), 3)}
    ov = [len(main_sel[k][0] & mom_sel[k][0]) + len(main_sel[k][1] & mom_sel[k][1]) for k in range(K)]
    res["anti_momentum_leg_overlap_mean_of_10"] = round(float(np.mean(ov)), 2)
    res["neighbours_x2_oos"] = {f"lookback_{L}d": st(run(sel[L], COST["x2"]).ret[oos_idx]) for L in (3, 14)}
    print("core runs done", flush=True)

    # BTC B&H and SMA200 CORE (weekly, same rebalance dates)
    jb = syms.index("BTCUSDT")
    btc_w = pd.Series([O[i + HOLD, jb] / O[i, jb] - 1 for i in weeks], index=x2.index)
    bc = pd.Series(C[:, jb])
    on = (bc > bc.rolling(200).mean()).shift(1, fill_value=False).values  # held on day d if close(d-1) > SMA200(d-1)
    dret = np.append(O[1:, jb] / O[:-1, jb] - 1, np.nan)
    sma_w = pd.Series([np.prod(1 + dret[i:i + HOLD] * on[i:i + HOLD]) - 1 for i in weeks], index=x2.index)
    res["bench_oos"] = {"btc_bh": st(btc_w[oos_idx]), "sma200_core": st(sma_w[oos_idx]),
                        "corr_card_vs_sma200": round(float(np.corrcoef(oo.ret, sma_w[oos_idx])[0, 1]), 3),
                        "corr_card_vs_btc": round(float(np.corrcoef(oo.ret, btc_w[oos_idx])[0, 1]), 3)}
    state = pd.Series([bool(on[i]) for i in weeks], index=x2.index)
    res["oos_by_sma200_state_x2"] = {"above": st(oo.ret[state[oos_idx]]), "below": st(oo.ret[~state[oos_idx]])}

    # random nulls (pre-cost: price + funding), OOS weeks only
    gross = runs["gross"].ret[oos_idx]
    om_g = float(gross.mean())
    ko = [k for k in range(K) if oos_mask[k]]
    Lr = np.full((len(ko), UNIV_N), np.nan)
    Sr = np.full((len(ko), UNIV_N), np.nan)
    for a, k in enumerate(ko):
        for b, s in enumerate(univ[k]):
            g = legs[(k, s)]
            Lr[a, b], Sr[a, b] = g["lp"] + g["lf"], g["sp"] + g["sf"]
    rng = np.random.default_rng(SEED)

    def clustered(rng):
        keys = rng.random((N_RANDOM, len(ko), UNIV_N))
        keys[:, np.isnan(Lr)] = np.inf
        idx = np.argsort(keys, axis=2)
        lv = np.take_along_axis(np.broadcast_to(Lr, keys.shape), idx[:, :, :LEGS], 2).mean(2)
        sv = np.take_along_axis(np.broadcast_to(Sr, keys.shape), idx[:, :, LEGS:2 * LEGS], 2).mean(2)
        return ((lv + sv) / 2).mean(1)

    dist = clustered(rng)
    other = [pct_rank(om_g, list(clustered(np.random.default_rng(SEED + s)))) for s in range(1, 5)]
    pl, ps = Lr[~np.isnan(Lr)], Sr[~np.isnan(Sr)]
    ind = (pl[rng.integers(len(pl), size=(N_RANDOM, len(ko) * LEGS))].mean(1) + ps[rng.integers(len(ps), size=(N_RANDOM, len(ko) * LEGS))].mean(1)) / 2
    q = lambda v, p: round(float(np.percentile(v, p)) * 100, 4)
    res["random_oos_precost"] = {
        "card_mean_precost_pct": round(om_g * 100, 4),
        "date_clustered": {"pct_rank": pct_rank(om_g, list(dist)), "p50_pct": q(dist, 50), "p95_pct": q(dist, 95), "p99_pct": q(dist, 99),
                           "other_seeds_pct_rank": other},
        "independent_pooled_legs": {"pct_rank": pct_rank(om_g, list(ind)), "p50_pct": q(ind, 50), "p95_pct": q(ind, 95), "p99_pct": q(ind, 99)},
    }
    print("random done", flush=True)

    o = res["stats_x2"]["oos"]
    lb = res["legs_x2"]["oos"]
    rc = res["random_oos_precost"]["date_clustered"]["pct_rank"]
    nb = [res["neighbours_x2_oos"][k]["mean_pct"] for k in res["neighbours_x2_oos"]]
    checks = {
        "oos_pf_x2_ge_1.1": (o["pf"] or 0) >= 1.1,
        "oos_mean_x2_gt_0": o["mean_pct"] > 0,
        "random_clustered_ge_95_card": rc >= 95,
        "beats_anti_momentum_oos": o["mean_pct"] > res["anti_momentum_x2"]["oos"]["mean_pct"],
        "decomposition_ok": not (lb["portfolio_price_pct"] < 0 and lb["portfolio_funding_pct"] < lb["portfolio_cost_pct"]),
        "neighbours_same_sign": all((v > 0) == (o["mean_pct"] > 0) for v in nb),
        "sharpe_ge_btc_bh_oos": (o["sharpe_ann"] or -9) >= (res["bench_oos"]["btc_bh"]["sharpe_ann"] or -9),
    }
    res["checks"] = checks
    res["random_clustered_ge_99_board"] = rc >= 99
    res["note_corr_sma200_gt_0.5"] = res["bench_oos"]["corr_card_vs_sma200"] > 0.5
    res["verdict"] = "KILL" if not all(checks.values()) else ("SURVIVE" if rc >= 99 else "PARTIAL")
    res["weekly_x2"] = [{"t": str(t.date()), "ret": round(r.ret, 6), "longs": sorted(main_sel[k][0]), "shorts": sorted(main_sel[k][1])}
                        for k, (t, r) in enumerate(x2.iterrows())]
    path = write_json(SLUG, res)
    for kk, v in res.items():
        if kk not in ("weekly_x2", "dedupe_drops", "decisions"):
            print(kk, v)
    print("dedupe drops", len(dedup_drops))
    print(path)


if __name__ == "__main__":
    sys.exit(main())
