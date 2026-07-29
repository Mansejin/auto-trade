#!/usr/bin/env python3
"""AE13b — Fee/slippage stress on frozen AE13 H_rich fade (no threshold mining).

Frozen H_rich: premium >= AE13 train 90th ≈ 0.004563 → fade (short) next UTC-day KRW-BTC.
Apply constant round-trip cost ladders; do NOT refit the rich cut on full sample.
Promote: never from this script alone.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "reports" / "improve" / "ae13b-fee-stress.json"
OUT_MD = ROOT / "reports" / "improve" / "20260729-ae13b-fee-stress.md"

# Frozen from AE13 train 90th — do not recompute / refit.
FROZEN_RICH_CUT = 0.004563296109377913
TRAIN_FRAC = 0.70
FEE_LADDER_BPS = [10, 20, 30, 50]
PRIMARY_BPS = 20


def get_json(url: str):
    req = urllib.request.Request(
        url, headers={"User-Agent": "ae13b-fee-stress", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def fetch_days(market: str, want: int = 2500) -> dict[str, float]:
    rows: list[dict] = []
    to = None
    while len(rows) < want:
        url = f"https://api.upbit.com/v1/candles/days?market={market}&count=200"
        if to:
            url += f"&to={to}"
        batch = get_json(url)
        if not batch:
            break
        rows.extend(batch)
        to = batch[-1]["candle_date_time_utc"]
        time.sleep(0.12)
        if len(batch) < 200:
            break
    return {c["candle_date_time_utc"][:10]: float(c["trade_price"]) for c in rows}


def stats(rets: list[float]) -> dict:
    if not rets:
        return {"n": 0}
    hits = sum(1 for r in rets if r > 0)
    return {
        "n": len(rets),
        "hit_rate": round(hits / len(rets), 4),
        "mean_pct": round(100 * sum(rets) / len(rets), 4),
        "median_pct": round(100 * sorted(rets)[len(rets) // 2], 4),
    }


def main() -> int:
    print("Fetching KRW-BTC / USDT-BTC / KRW-USDT days...")
    krw_btc = fetch_days("KRW-BTC")
    usdt_btc = fetch_days("USDT-BTC")
    krw_usdt = fetch_days("KRW-USDT")
    common = sorted(set(krw_btc) & set(usdt_btc) & set(krw_usdt))
    rows = []
    for i, d in enumerate(common[:-1]):
        nxt = common[i + 1]
        prem = krw_btc[d] / (usdt_btc[d] * krw_usdt[d]) - 1.0
        fwd = krw_btc[nxt] / krw_btc[d] - 1.0
        rows.append({"date": d, "premium": prem, "fwd_1d": fwd})

    cut = int(len(rows) * TRAIN_FRAC)
    hold_days = rows[cut:]
    rich_ev = [r for r in hold_days if r["premium"] >= FROZEN_RICH_CUT]
    if not rich_ev:
        print("No holdout rich events — abort")
        return 1

    # Fade = short next-day KRW-BTC. Gross fade PnL = -fwd_1d.
    fade_gross = [-e["fwd_1d"] for e in rich_ev]
    # Always-short baseline over the same holdout calendar span.
    lo, hi = min(e["date"] for e in rich_ev), max(e["date"] for e in rich_ev)
    base_fwds = [r["fwd_1d"] for r in rows if lo <= r["date"] <= hi]
    base_fade = [-x for x in base_fwds]
    gross = stats(fade_gross)
    base = stats(base_fade)
    # Directional: fade "hit" = price down (fwd < 0) on event days
    fade_dir_hit = round(sum(1 for e in rich_ev if e["fwd_1d"] < 0) / len(rich_ev), 4)
    base_dir_hit = (
        round(sum(1 for x in base_fwds if x < 0) / len(base_fwds), 4) if base_fwds else 0.0
    )

    ladder = []
    primary_ok = False
    for bps in FEE_LADDER_BPS:
        fee = bps / 10000.0
        net_rets = [g - fee for g in fade_gross]
        st = stats(net_rets)
        net_pos_hit = (
            round(sum(1 for r in net_rets if r > 0) / len(net_rets), 4) if net_rets else 0
        )
        mean_ok = st.get("mean_pct", -999) > base.get("mean_pct", 0)
        hit_ok = fade_dir_hit > base_dir_hit
        survives = bool(mean_ok and hit_ok and rich_ev)
        if bps == PRIMARY_BPS:
            primary_ok = survives
        ladder.append(
            {
                "rt_bps": bps,
                "holdout_net": st,
                "net_positive_hit": net_pos_hit,
                "vs_baseline_mean": mean_ok,
                "vs_baseline_dir_hit": hit_ok,
                "survives": survives,
            }
        )

    verdict = "SURVIVES_PRIMARY_FEE" if primary_ok else "FAILS_PRIMARY_FEE"
    payload = {
        "id": "AE13b",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frozen_rich_cut": FROZEN_RICH_CUT,
        "definition": "premium = KRW-BTC/(USDT-BTC*KRW-USDT)-1; fade = short next-day",
        "overlap_days": len(common),
        "series_n": len(rows),
        "holdout_days": len(hold_days),
        "holdout_rich_n": len(rich_ev),
        "holdout_fade_gross": gross,
        "holdout_baseline_always_short": base,
        "fade_dir_hit": fade_dir_hit,
        "baseline_down_hit": base_dir_hit,
        "primary_rt_bps": PRIMARY_BPS,
        "ladder": ladder,
        "verdict": verdict,
        "promote": False,
        "note": (
            "Surviving fee stress != LIVE promote. Cut frozen from AE13 train 90th; "
            "no refit. Paper micro-size only after human approve."
        ),
        "anti_overfit": [
            "frozen rich cut from AE13 (no full-sample refit)",
            "same 70/30 time split as AE13 for holdout events",
            "fee ladder only; no threshold mining",
            "H2 OB path deferred (collect missing locally)",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    rows_md = [
        "| RT bps | Net mean % | Net>0 hit | Fade dir hit | Base short mean | Base down hit | Survives |",
        "|-------:|-----------:|----------:|-------------:|----------------:|--------------:|:--------:|",
    ]
    for x in ladder:
        n = x["holdout_net"]
        rows_md.append(
            f"| {x['rt_bps']} | {n.get('mean_pct')} | {x['net_positive_hit']} | "
            f"{fade_dir_hit} | {base.get('mean_pct')} | {base_dir_hit} | "
            f"{'Y' if x['survives'] else 'N'} |"
        )

    md = f"""# AE13b — Fee stress on AE13 H_rich fade (frozen)

> Same frozen rich cut (`premium >= {FROZEN_RICH_CUT}` from AE13 train 90th).  
> Same time holdout (last {int((1 - TRAIN_FRAC) * 100)}% of premium series).  
> Action assumed for costing: **short** next-day KRW-BTC (fade). Baseline = always-short in the same window.  
> **No cut refit. No LIVE promote.**

## Hypothesis (frozen before scoring)

On holdout days with Upbit BTC premium ≥ frozen rich cut, a 1-day fade (short) still beats always-short **after** primary round-trip costs.

## Primary gate

Round-trip **{PRIMARY_BPS} bps** (≈ Upbit 5+5 fee + ~10 slip). Survive if holdout **net fade mean > always-short baseline mean** and **fade directional hit (price down) > baseline down-hit**.

## Results

Holdout rich n={len(rich_ev)}. Gross fade mean %={gross.get('mean_pct')}, fade dir hit={fade_dir_hit}.  
Baseline always-short mean %={base.get('mean_pct')}, down hit={base_dir_hit}.

{chr(10).join(rows_md)}

## Verdict

**{verdict}**

Promotion: **No.** Optional human paper micro-size only if primary survives — still outside Policy C map. H2 OB study remains blocked until collect ≥336 rows.

Raw: `reports/improve/ae13b-fee-stress.json`
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
