#!/usr/bin/env python3
"""AE13 — Upbit internal BTC premium event study (orthogonal to funding/TA scrapes).

Premium = KRW-BTC / (USDT-BTC * KRW-USDT) - 1
(Requires KRW-USDT history; available from ~2024-06 on Upbit.)

Frozen hypotheses (declared before looking at holdout):
  H_rich: premium >= train 90th pct → next-day KRW-BTC mean & hit < baseline
          (fade rich KRW premium)
  H_cheap: premium <= train 10th pct → next-day KRW-BTC mean & hit > baseline
          (bounce cheap KRW premium)

Anti-overfit:
  - Time-split series 70/30 for percentile fit vs holdout scoring
  - Percentiles from train premiums only
  - No return-based threshold search; no LIVE promote
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "reports" / "improve" / "ae13-upbit-premium.json"
OUT_MD = ROOT / "reports" / "improve" / "20260729-ae13-upbit-premium.md"

TRAIN_FRAC = 0.70
RICH_Q = 0.90
CHEAP_Q = 0.10
MIN_HOLDOUT_EVENTS = 8


def get_json(url: str):
    req = urllib.request.Request(
        url, headers={"User-Agent": "ae13-premium", "Accept": "application/json"}
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


def percentile(xs: list[float], q: float) -> float:
    if not xs:
        raise ValueError("empty")
    ys = sorted(xs)
    if len(ys) == 1:
        return ys[0]
    pos = q * (len(ys) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(ys) - 1)
    w = pos - lo
    return ys[lo] * (1 - w) + ys[hi] * w


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


def baseline(fwd: dict[str, float], dates: list[str]) -> dict:
    if not dates:
        return {"n": 0}
    lo, hi = min(dates), max(dates)
    rs = [fwd[d] for d in sorted(fwd) if lo <= d <= hi]
    return stats(rs)


def score_hyp(name: str, events: list[dict], fwd: dict[str, float], fade: bool) -> dict:
    """fade=True expects underperformance vs baseline; else outperformance."""
    if len(events) < MIN_HOLDOUT_EVENTS:
        return {
            "id": name,
            "verdict": "NOT_READY",
            "reason": f"holdout_events={len(events)}<{MIN_HOLDOUT_EVENTS}",
            "events": len(events),
        }
    rets = [e["fwd_1d"] for e in events]
    st = stats(rets)
    base = baseline(fwd, [e["date"] for e in events])
    reasons = []
    falsified = False
    if fade:
        if st["mean_pct"] >= base.get("mean_pct", 0):
            falsified = True
            reasons.append("holdout_mean>=baseline_mean")
        if st["hit_rate"] >= base.get("hit_rate", 0):
            falsified = True
            reasons.append("holdout_hit>=baseline_hit")
    else:
        if st["mean_pct"] <= base.get("mean_pct", 0):
            falsified = True
            reasons.append("holdout_mean<=baseline_mean")
        if st["hit_rate"] <= base.get("hit_rate", 0):
            falsified = True
            reasons.append("holdout_hit<=baseline_hit")
    return {
        "id": name,
        "events": len(events),
        "stats": st,
        "baseline": base,
        "verdict": "FALSIFIED" if falsified else "RETAINED_for_research",
        "falsified": falsified,
        "reasons": reasons,
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
        # only consecutive calendar pairs that exist as next trading day in series
        if nxt != common[i + 1]:
            continue
        prem = krw_btc[d] / (usdt_btc[d] * krw_usdt[d]) - 1.0
        fwd = krw_btc[nxt] / krw_btc[d] - 1.0
        rows.append({"date": d, "premium": prem, "fwd_1d": fwd})

    cut = int(len(rows) * TRAIN_FRAC)
    train, hold_days = rows[:cut], rows[cut:]
    rich_cut = percentile([r["premium"] for r in train], RICH_Q)
    cheap_cut = percentile([r["premium"] for r in train], CHEAP_Q)

    rich_ev = [r for r in hold_days if r["premium"] >= rich_cut]
    cheap_ev = [r for r in hold_days if r["premium"] <= cheap_cut]
    fwd_map = {r["date"]: r["fwd_1d"] for r in rows}

    h_rich = score_hyp("H_rich_fade", rich_ev, fwd_map, fade=True)
    h_cheap = score_hyp("H_cheap_bounce", cheap_ev, fwd_map, fade=False)

    overall = "FAIL"
    if h_rich.get("verdict") == "RETAINED_for_research" or h_cheap.get("verdict") == "RETAINED_for_research":
        overall = "PARTIAL_RETAIN"
    if h_rich.get("falsified") and h_cheap.get("falsified"):
        overall = "FALSIFIED"
    if h_rich.get("verdict") == "NOT_READY" and h_cheap.get("verdict") == "NOT_READY":
        overall = "NOT_READY"

    payload = {
        "id": "AE13",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "definition": "premium = KRW-BTC/(USDT-BTC*KRW-USDT)-1",
        "overlap_days": len(common),
        "series_n": len(rows),
        "train_n": len(train),
        "holdout_days": len(hold_days),
        "train_rich_90pct": rich_cut,
        "train_cheap_10pct": cheap_cut,
        "H_rich": h_rich,
        "H_cheap": h_cheap,
        "overall": overall,
        "promote": False,
        "anti_overfit": [
            f"train first {int(TRAIN_FRAC*100)}% by time for percentiles only",
            "holdout last 30% scored once",
            "no return-based threshold search",
            "orthogonal to AE6–AE11 TA and AE7/AE12 funding",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    def blk(tag: str, r: dict) -> str:
        lines = [f"### {tag} — **{r.get('verdict')}**", ""]
        if r.get("reason"):
            lines.append(f"Reason: `{r['reason']}`")
        if r.get("reasons"):
            lines.append("Reasons: " + ", ".join(f"`{x}`" for x in r["reasons"]))
        if r.get("stats"):
            s, b = r["stats"], r["baseline"]
            lines += [
                "",
                f"n={s.get('n')} mean%={s.get('mean_pct')} hit={s.get('hit_rate')} | "
                f"baseline mean%={b.get('mean_pct')} hit={b.get('hit_rate')}",
            ]
        lines.append("")
        return "\n".join(lines)

    md = f"""# AE13 — Upbit internal BTC premium (orthogonal alt-data)

> Premium = `KRW-BTC / (USDT-BTC × KRW-USDT) − 1`.  
> Train ({int(TRAIN_FRAC*100)}%) fits rich/cheap percentiles; holdout scores once.  
> Not investment advice. **No LIVE / Policy C promote.**

## Hypotheses (frozen)

1. **H_rich:** premium ≥ train 90th (= `{rich_cut:.6f}`) → next-day KRW-BTC **underperforms** baseline  
2. **H_cheap:** premium ≤ train 10th (= `{cheap_cut:.6f}`) → next-day KRW-BTC **outperforms** baseline  

Overlap days: {len(common)}. Series n={len(rows)}. Holdout days={len(hold_days)}.

{blk("H_rich fade", h_rich)}
{blk("H_cheap bounce", h_cheap)}

## Overall

**{overall}**

Promotion: **No.**

Raw: `reports/improve/ae13-upbit-premium.json`
"""
    OUT_MD.write_text(md)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
