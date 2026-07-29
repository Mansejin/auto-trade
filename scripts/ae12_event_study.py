#!/usr/bin/env python3
"""AE12b event study — frozen hypotheses only.

H1: fundingRate <= -0.0002 → next UTC-day KRW-BTC mean return & hit-rate > baseline
H2: |Upbit orderbook imbalance| >= 0.4 → next 1h signed return beats baseline
    (sign of imbalance); requires forward-collected JSONL.

Holdout rule (frozen): last 30% of event timestamps by time.

H1 historical source: HTX (Huobi) BTC-USDT funding history — deeper than OKX/Bitget
in this environment. Forward collector may still log OKX; do not mix sources inside
one test without an explicit new AE id.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECT = ROOT / "reports" / "ae12-collect"
FUNDING_LOG = COLLECT / "okx-funding.jsonl"
ORDERBOOK_LOG = COLLECT / "upbit-orderbook.jsonl"
OUT_JSON = ROOT / "reports" / "improve" / "ae12b-event-study.json"
OUT_MD = ROOT / "reports" / "improve" / "20260729-ae12b-event-study.md"
STATUS = COLLECT / "event-study-status.json"

# Frozen — do not change after AE12 declaration
H1_THRESH = -0.0002
H2_IMB = 0.4
HOLDOUT_FRAC = 0.30
MIN_HOLDOUT_EVENTS = 8
MIN_OB_ROWS_FOR_H2 = 24 * 14  # ~2 weeks at hourly; soft gate


def get_json(url: str):
    req = urllib.request.Request(
        url, headers={"User-Agent": "ae12b-event-study", "Accept": "application/json"}
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
            ts = int(x["funding_time"])
            fr = float(x["funding_rate"])
            rows.append((ts, fr))
        total_page = int((d.get("data") or {}).get("total_page") or page)
        if page >= total_page:
            break
        time.sleep(0.08)
    by = {t: fr for t, fr in rows}
    return sorted(by.items())


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


def fetch_upbit_minutes(want: int = 200) -> list[dict]:
    """Recent 60m candles only (Upbit max 200). For H2 forward path."""
    url = "https://api.upbit.com/v1/candles/minutes/60?market=KRW-BTC&count=200"
    batch = get_json(url)
    return list(reversed(batch)) if batch else []


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


def split_holdout(items: list, frac: float = HOLDOUT_FRAC):
    if not items:
        return [], []
    cut = int(len(items) * (1.0 - frac))
    cut = min(max(cut, 0), len(items))
    return items[:cut], items[cut:]


def run_h1() -> dict:
    funding = fetch_htx_funding()
    by_day = fetch_upbit_days()
    fwd = day_fwd(by_day)
    events = []
    for ts, fr in funding:
        if fr > H1_THRESH:
            continue
        d = datetime.fromtimestamp(ts / 1000.0, UTC).strftime("%Y-%m-%d")
        if d not in fwd:
            continue
        events.append({"ts": ts, "date": d, "funding": fr, "fwd_1d": fwd[d]})
    events.sort(key=lambda e: e["ts"])
    train, hold = split_holdout(events)
    if not events:
        return {
            "id": "H1",
            "verdict": "UNTESTABLE",
            "reason": "zero_events_at_frozen_threshold",
            "threshold": H1_THRESH,
            "funding_points": len(funding),
            "source": "HTX BTC-USDT",
        }
    tr_s = stats([e["fwd_1d"] for e in train])
    ho_s = stats([e["fwd_1d"] for e in hold])
    tr_dates = [e["date"] for e in train] or ["9999"]
    ho_dates = [e["date"] for e in hold] or ["9999"]
    tr_b = baseline_days(fwd, min(tr_dates), max(tr_dates)) if train else {"n": 0}
    ho_b = baseline_days(fwd, min(ho_dates), max(ho_dates)) if hold else {"n": 0}

    reasons = []
    falsified = False
    if ho_s.get("n", 0) < MIN_HOLDOUT_EVENTS:
        falsified = True
        reasons.append(f"holdout_n_too_small={ho_s.get('n')}")
    else:
        if ho_s["mean_pct"] <= ho_b.get("mean_pct", 0):
            falsified = True
            reasons.append("holdout_mean<=baseline_mean")
        if ho_s["hit_rate"] <= ho_b.get("hit_rate", 0):
            falsified = True
            reasons.append("holdout_hit_rate<=baseline")

    return {
        "id": "H1",
        "source": "HTX BTC-USDT funding history",
        "threshold": H1_THRESH,
        "funding_points": len(funding),
        "events_total": len(events),
        "train": {"stats": tr_s, "baseline": tr_b},
        "holdout": {"stats": ho_s, "baseline": ho_b},
        "verdict": "FALSIFIED" if falsified else "RETAINED_for_research",
        "falsified": falsified,
        "reasons": reasons,
        "anti_overfit": [
            f"threshold frozen at {H1_THRESH}",
            f"holdout last {int(HOLDOUT_FRAC*100)}% of events by time",
            "no threshold sweep",
        ],
    }


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.open())


def run_h2() -> dict:
    n = count_lines(ORDERBOOK_LOG)
    base = {
        "id": "H2",
        "threshold_abs_imbalance": H2_IMB,
        "orderbook_rows": n,
        "min_rows": MIN_OB_ROWS_FOR_H2,
        "source_log": str(ORDERBOOK_LOG.relative_to(ROOT)),
    }
    if n < MIN_OB_ROWS_FOR_H2:
        return {
            **base,
            "verdict": "NOT_READY",
            "reason": "insufficient_forward_orderbook_rows",
            "message": "keep running ae12_forward_collect.py; do not mine imbalance cut",
        }

    # Align snapshots to next 1h close when enough history exists
    candles = fetch_upbit_minutes(200)
    if len(candles) < 10:
        return {**base, "verdict": "NOT_READY", "reason": "insufficient_1h_candles"}

    by_hour = {}
    for c in candles:
        # candle_date_time_utc is start of hour
        by_hour[c["candle_date_time_utc"][:13]] = float(c["trade_price"])  # YYYY-MM-DDTHH

    # build hour returns
    hours = sorted(by_hour)
    fwd_h = {}
    for i in range(len(hours) - 1):
        fwd_h[hours[i]] = by_hour[hours[i + 1]] / by_hour[hours[i]] - 1.0

    events = []
    with ORDERBOOK_LOG.open() as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            imb = rec.get("imbalance")
            if imb is None or abs(imb) < H2_IMB:
                continue
            ts = rec.get("ts_utc") or ""
            key = ts[:13]  # YYYY-MM-DDTHH
            if key not in fwd_h:
                continue
            signed = fwd_h[key] if imb > 0 else -fwd_h[key]
            # hypothesis: imbalance sign predicts next hour direction → signed ret > 0 more often
            events.append({"ts": ts, "imbalance": imb, "signed_next_1h": signed, "raw_next_1h": fwd_h[key]})

    events.sort(key=lambda e: e["ts"])
    train, hold = split_holdout(events)
    if len(hold) < MIN_HOLDOUT_EVENTS:
        return {
            **base,
            "verdict": "NOT_READY",
            "reason": f"holdout_events={len(hold)}<{MIN_HOLDOUT_EVENTS}",
            "events_total": len(events),
        }

    def signed_stats(ev):
        rets = [e["signed_next_1h"] for e in ev]
        return stats(rets)

    # baseline: random-sign expectancy ~0; use unsigned |ret| mean as alternate — stick to hit_rate of signed>0 vs 0.5
    tr_s, ho_s = signed_stats(train), signed_stats(hold)
    reasons = []
    falsified = False
    if ho_s["mean_pct"] <= 0:
        falsified = True
        reasons.append("holdout_signed_mean<=0")
    if ho_s["hit_rate"] <= 0.5:
        falsified = True
        reasons.append("holdout_hit_rate<=0.5")

    return {
        **base,
        "events_total": len(events),
        "train": tr_s,
        "holdout": ho_s,
        "verdict": "FALSIFIED" if falsified else "RETAINED_for_research",
        "falsified": falsified,
        "reasons": reasons,
        "anti_overfit": [
            f"|imbalance| threshold frozen at {H2_IMB}",
            f"holdout last {int(HOLDOUT_FRAC*100)}% by time",
            "baseline hit_rate=0.5 (no direction mining)",
        ],
    }


def main() -> int:
    print("Running H1 (HTX funding)...")
    h1 = run_h1()
    print(json.dumps(h1, ensure_ascii=False, indent=2))
    print("Running H2 (orderbook forward)...")
    h2 = run_h2()
    print(json.dumps(h2, ensure_ascii=False, indent=2))

    payload = {
        "id": "AE12b",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "H1": h1,
        "H2": h2,
        "promote": False,
        "note": "No LIVE/Policy map changes from this study.",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    def blk(tag: str, r: dict) -> str:
        v = r.get("verdict")
        lines = [f"### {tag} — **{v}**", ""]
        if r.get("reason"):
            lines.append(f"Reason: `{r['reason']}`")
        if r.get("reasons"):
            lines.append("Reasons: " + ", ".join(f"`{x}`" for x in r["reasons"]))
        if r.get("train") and isinstance(r["train"], dict) and "stats" in r["train"]:
            tr, ho = r["train"], r["holdout"]
            lines += [
                "",
                "| Set | n | Mean % | Hit | Baseline mean | Baseline hit |",
                "|-----|--:|-------:|----:|--------------:|-------------:|",
                f"| Train | {tr['stats'].get('n')} | {tr['stats'].get('mean_pct')} | {tr['stats'].get('hit_rate')} | {tr['baseline'].get('mean_pct')} | {tr['baseline'].get('hit_rate')} |",
                f"| Holdout | {ho['stats'].get('n')} | {ho['stats'].get('mean_pct')} | {ho['stats'].get('hit_rate')} | {ho['baseline'].get('mean_pct')} | {ho['baseline'].get('hit_rate')} |",
            ]
        elif r.get("holdout") and isinstance(r.get("holdout"), dict) and "n" in r["holdout"]:
            lines += [
                "",
                f"Holdout n={r['holdout'].get('n')} mean%={r['holdout'].get('mean_pct')} hit={r['holdout'].get('hit_rate')}",
            ]
        lines.append("")
        return "\n".join(lines)

    md = f"""# AE12b — Frozen funding / orderbook event study

> Thresholds and holdout rule frozen at AE12 declaration.  
> H1 uses **HTX** historical funding (deep history). H2 needs forward Upbit orderbook JSONL.  
> Not investment advice. Fees/slippage not modeled.

## Hypotheses (frozen)

1. **H1:** `fundingRate <= -0.0002` → next UTC day KRW-BTC mean & hit-rate > same-window baseline  
2. **H2:** `|orderbook imbalance| >= 0.4` → next 1h move in imbalance direction beats hit-rate 0.5  

Holdout: last **30%** of events by time. Min holdout events: **{MIN_HOLDOUT_EVENTS}**.

{blk("H1 Funding", h1)}
{blk("H2 Orderbook", h2)}

## Promotion

**No.** AE12b does not change Policy C or LIVE `STRATEGY_PATH`.

Raw: `reports/improve/ae12b-event-study.json`
"""
    OUT_MD.write_text(md)

    status = {
        "ready": h1.get("verdict") not in {"UNTESTABLE"} or h2.get("verdict") not in {"NOT_READY"},
        "H1": h1.get("verdict"),
        "H2": h2.get("verdict"),
        "updated_at": payload["updated_at"],
    }
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    # status jsonl is gitignored; still write for local/VPS
    try:
        STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    except OSError:
        pass

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    # exit 0 always after study run; readiness exit code was for stub
    return 0


if __name__ == "__main__":
    sys.exit(main())
