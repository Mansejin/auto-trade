#!/usr/bin/env python3
"""AE12c — Fee/slippage stress on frozen AE12b H1 (no threshold mining).

Frozen H1: HTX fundingRate <= -0.0002 → next UTC-day KRW-BTC return.
Apply constant round-trip cost ladders; do not retune funding cut.
Promote: never from this script alone.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "reports" / "improve" / "ae12c-fee-stress.json"
OUT_MD = ROOT / "reports" / "improve" / "20260729-ae12c-fee-stress.md"

H1_THRESH = -0.0002
HOLDOUT_FRAC = 0.30
# Frozen cost ladder (fraction of notional, round-trip). Includes fee + slippage budget.
# Primary gate: 20 bps RT (Upbit ~5+5 bps fee + ~10 bps slip).
FEE_LADDER_BPS = [10, 20, 30, 50]
PRIMARY_BPS = 20


def get_json(url: str):
    req = urllib.request.Request(
        url, headers={"User-Agent": "ae12c-fee-stress", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def fetch_htx_funding() -> list[tuple[int, float]]:
    rows: list[tuple[int, float]] = []
    for page in range(1, 250):
        url = (
            "https://api.hbdm.com/linear-swap-api/v1/swap_historical_funding_rate"
            f"?contract_code=BTC-USDT&page_index={page}&page_size=50"
        )
        d = get_json(url)
        batch = (d.get("data") or {}).get("data") or []
        if not batch:
            break
        for x in batch:
            rows.append((int(x["funding_time"]), float(x["funding_rate"])))
        total_page = int((d.get("data") or {}).get("total_page") or page)
        if page >= total_page:
            break
        time.sleep(0.08)
    return sorted({t: fr for t, fr in rows}.items())


def fetch_upbit_days(want: int = 2500) -> dict[str, float]:
    rows: list[dict] = []
    to = None
    while len(rows) < want:
        url = "https://api.upbit.com/v1/candles/days?market=KRW-BTC&count=200"
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


def day_fwd(by_day: dict[str, float]) -> dict[str, float]:
    days = sorted(by_day)
    return {days[i]: by_day[days[i + 1]] / by_day[days[i]] - 1.0 for i in range(len(days) - 1)}


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


def baseline_days(fwd: dict[str, float], lo: str, hi: str) -> dict:
    rs = [fwd[d] for d in sorted(fwd) if lo <= d <= hi]
    return stats(rs)


def main() -> int:
    print("Fetching HTX funding + Upbit days...")
    funding = fetch_htx_funding()
    fwd = day_fwd(fetch_upbit_days())
    events = []
    for ts, fr in funding:
        if fr > H1_THRESH:
            continue
        d = datetime.fromtimestamp(ts / 1000.0, UTC).strftime("%Y-%m-%d")
        if d not in fwd:
            continue
        events.append({"ts": ts, "date": d, "funding": fr, "fwd_1d": fwd[d]})
    events.sort(key=lambda e: e["ts"])
    cut = int(len(events) * (1.0 - HOLDOUT_FRAC))
    hold = events[cut:]
    ho_dates = [e["date"] for e in hold]
    base = baseline_days(fwd, min(ho_dates), max(ho_dates)) if hold else {"n": 0}
    gross = stats([e["fwd_1d"] for e in hold])

    ladder = []
    primary_ok = False
    for bps in FEE_LADDER_BPS:
        fee = bps / 10000.0
        net_rets = [e["fwd_1d"] - fee for e in hold]
        st = stats(net_rets)
        # Directional hit unchanged by constant fee; net-positive hit can drop
        net_pos_hit = (
            round(sum(1 for r in net_rets if r > 0) / len(net_rets), 4) if net_rets else 0
        )
        mean_ok = st.get("mean_pct", -999) > base.get("mean_pct", 0)
        # Keep AE12b directional hit gate vs baseline (gross price direction)
        hit_ok = gross.get("hit_rate", 0) > base.get("hit_rate", 0)
        survives = bool(mean_ok and hit_ok and hold)
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
    # Still research-only; no promote even if survives
    payload = {
        "id": "AE12c",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "threshold": H1_THRESH,
        "source": "HTX BTC-USDT",
        "events_total": len(events),
        "holdout_n": len(hold),
        "holdout_gross": gross,
        "holdout_baseline": base,
        "primary_rt_bps": PRIMARY_BPS,
        "ladder": ladder,
        "verdict": verdict,
        "promote": False,
        "note": "Surviving fee stress ≠ LIVE promote. Paper micro-size only after human approve.",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    rows = [
        "| RT bps | Net mean % | Net>0 hit | Gross hit | Base mean | Base hit | Survives |",
        "|-------:|-----------:|----------:|----------:|----------:|---------:|:--------:|",
    ]
    for x in ladder:
        n = x["holdout_net"]
        rows.append(
            f"| {x['rt_bps']} | {n.get('mean_pct')} | {x['net_positive_hit']} | "
            f"{gross.get('hit_rate')} | {base.get('mean_pct')} | {base.get('hit_rate')} | "
            f"{'Y' if x['survives'] else 'N'} |"
        )

    md = f"""# AE12c — Fee stress on AE12b H1 (frozen)

> Same HTX funding cut (`<= {H1_THRESH}`), same time holdout ({int(HOLDOUT_FRAC*100)}%).  
> Only cost assumption changes. **No threshold mining. No LIVE promote.**

## Primary gate

Round-trip **{PRIMARY_BPS} bps** (≈ Upbit 5+5 fee + ~10 slip). Survive if holdout **net mean > baseline mean** and **gross directional hit > baseline hit**.

## Results

Holdout n={len(hold)}. Gross mean %={gross.get('mean_pct')}, hit={gross.get('hit_rate')}.

{chr(10).join(rows)}

## Verdict

**{verdict}**

Promotion: **No.** Optional human paper micro-size only if primary survives — still outside Policy C map.

Raw: `reports/improve/ae12c-fee-stress.json`
"""
    OUT_MD.write_text(md)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
