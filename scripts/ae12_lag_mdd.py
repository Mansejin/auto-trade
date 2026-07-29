#!/usr/bin/env python3
"""AE12: Policy C regime-switch lag MDD (daily KRW-BTC).

Measures drawdown in the first L days after a labeled regime change —
the cost window while lagging SMA/ADX classifiers are still catching up.

Does NOT retune regime rules or strategy JSON. Stdlib only.
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEG_PATH = ROOT / "reports" / "regimes-krw-btc-1d-5y.json"
OUT_JSON = ROOT / "reports" / "improve" / "ae12-lag-mdd.json"
OUT_MD = ROOT / "reports" / "improve" / "20260729-ae12-lag-mdd.md"
LAGS = (3, 5, 7, 10, 14)
RISK_OFF = {"bear", "sideways"}
RISK_ON = {"bull", "transition"}


def fetch_days(want: int = 2000) -> dict[str, float]:
    rows: list[dict] = []
    to = None
    while len(rows) < want:
        url = "https://api.upbit.com/v1/candles/days?market=KRW-BTC&count=200"
        if to:
            url += f"&to={to}"
        req = urllib.request.Request(
            url, headers={"Accept": "application/json", "User-Agent": "ae12-lag-mdd"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.loads(resp.read().decode())
        if not batch:
            break
        rows.extend(batch)
        to = batch[-1]["candle_date_time_utc"]
        time.sleep(0.12)
        if len(batch) < 200:
            break
    return {c["candle_date_time_utc"][:10]: float(c["trade_price"]) for c in rows}


def mdd_from_start(closes: list[float]) -> float:
    """Max drawdown from series start NAV=1 (fraction, <=0)."""
    if not closes:
        return 0.0
    peak = closes[0]
    mdd = 0.0
    for px in closes:
        if px > peak:
            peak = px
        dd = px / peak - 1.0
        if dd < mdd:
            mdd = dd
    return mdd


def window_closes(by_day: dict[str, float], start: str, lag: int) -> list[float] | None:
    days = sorted(by_day)
    if start not in by_day:
        # nearest next available
        later = [d for d in days if d >= start]
        if not later:
            return None
        start = later[0]
    i0 = days.index(start)
    i1 = min(i0 + lag, len(days) - 1)
    if i1 <= i0:
        return None
    return [by_day[d] for d in days[i0 : i1 + 1]]


def main() -> None:
    segs = json.loads(SEG_PATH.read_text())["segments"]
    by_day = fetch_days()
    events = []
    for prev, curr in zip(segs, segs[1:]):
        if prev["regime"] == curr["regime"]:
            continue
        switch = curr["start"]
        row: dict = {
            "switch": switch,
            "from": prev["regime"],
            "to": curr["regime"],
            "kind": (
                "risk_off"
                if curr["regime"] in RISK_OFF
                else "risk_on"
                if curr["regime"] in RISK_ON
                else "other"
            ),
            "lags": {},
        }
        for lag in LAGS:
            closes = window_closes(by_day, switch, lag)
            if not closes or len(closes) < 2:
                continue
            ret = closes[-1] / closes[0] - 1.0
            mdd = mdd_from_start(closes)
            row["lags"][str(lag)] = {
                "ret_pct": round(ret * 100, 3),
                "mdd_pct": round(mdd * 100, 3),
                "bars": len(closes),
            }
        events.append(row)

    def summarize(kind: str) -> dict:
        subset = [e for e in events if e["kind"] == kind]
        out: dict = {"n_switches": len(subset), "by_lag": {}}
        for lag in LAGS:
            mdds = [
                e["lags"][str(lag)]["mdd_pct"]
                for e in subset
                if str(lag) in e["lags"]
            ]
            rets = [
                e["lags"][str(lag)]["ret_pct"]
                for e in subset
                if str(lag) in e["lags"]
            ]
            if not mdds:
                continue
            mdds_s = sorted(mdds)
            out["by_lag"][str(lag)] = {
                "n": len(mdds),
                "mdd_median_pct": mdds_s[len(mdds_s) // 2],
                "mdd_worst_pct": min(mdds),
                "mdd_p25_pct": mdds_s[max(0, len(mdds_s) // 4)],
                "ret_median_pct": sorted(rets)[len(rets) // 2],
                "ret_mean_pct": round(sum(rets) / len(rets), 3),
            }
        return out

    # Materiality thresholds pre-registered (not fit on results)
    MATERIAL = {
        "risk_off_7d_median_mdd_lt": -5.0,  # more negative than -5% => material
        "risk_off_7d_worst_mdd_lt": -12.0,
    }
    risk_off = summarize("risk_off")
    risk_on = summarize("risk_on")
    lag7 = risk_off.get("by_lag", {}).get("7", {})
    material = bool(lag7) and (
        lag7.get("mdd_median_pct", 0) <= MATERIAL["risk_off_7d_median_mdd_lt"]
        or lag7.get("mdd_worst_pct", 0) <= MATERIAL["risk_off_7d_worst_mdd_lt"]
    )

    payload = {
        "id": "AE12_lag_mdd",
        "segments_file": str(SEG_PATH.relative_to(ROOT)),
        "n_segments": len(segs),
        "n_switches": len(events),
        "lags_days": list(LAGS),
        "materiality_pre_registered": MATERIAL,
        "lag_is_material_for_sizing": material,
        "risk_off_summary": risk_off,
        "risk_on_summary": risk_on,
        "worst_risk_off_events": sorted(
            [e for e in events if e["kind"] == "risk_off" and "7" in e["lags"]],
            key=lambda e: e["lags"]["7"]["mdd_pct"],
        )[:5],
        "note": (
            "MDD is buy&hold BTC from switch-day close over L days — "
            "proxy for cost of still being long while classifier lags into risk-off."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    def fmt_lag(summary: dict) -> str:
        lines = [
            "| L days | n | MDD median | MDD worst | Ret median | Ret mean |",
            "|-------:|--:|-----------:|----------:|-----------:|---------:|",
        ]
        for lag in LAGS:
            s = summary.get("by_lag", {}).get(str(lag))
            if not s:
                continue
            lines.append(
                f"| {lag} | {s['n']} | {s['mdd_median_pct']}% | {s['mdd_worst_pct']}% | "
                f"{s['ret_median_pct']}% | {s['ret_mean_pct']}% |"
            )
        return "\n".join(lines)

    worst_rows = []
    for e in payload["worst_risk_off_events"]:
        g = e["lags"]["7"]
        worst_rows.append(
            f"| {e['switch']} | {e['from']}→{e['to']} | {g['mdd_pct']}% | {g['ret_pct']}% |"
        )

    md = f"""# AE12 — Policy C regime-switch lag MDD

> Measures **buy&hold BTC drawdown** in the first L days after a daily regime label flip.  
> Proxy for “뒷북 전환” pain while SMA/ADX classifiers catch up.  
> **Does not** change Policy C rules. Not investment advice.

## Method

- Labels: `{SEG_PATH.name}` (engine v2, 5y segments)
- For each switch `from → to`, from switch-day close over L ∈ {list(LAGS)} days:
  - `ret`: end/start − 1
  - `mdd`: max drawdown of that window from its running peak
- **Risk-off** switches (`→ bear|sideways`): lag cost ≈ still long into weakness
- **Risk-on** switches (`→ bull|transition`): reported for context (missed upside if stayed defensive)

## Pre-registered materiality

Lag is “material for sizing” if risk-off **7d** median MDD ≤ **−5%** OR worst ≤ **−12%**.

## Risk-off switches ({risk_off['n_switches']})

{fmt_lag(risk_off)}

## Risk-on switches ({risk_on['n_switches']})

{fmt_lag(risk_on)}

## Worst risk-off 7d windows

| Switch | Transition | MDD 7d | Ret 7d |
|--------|------------|-------:|-------:|
{chr(10).join(worst_rows)}

## Verdict

**Lag material for sizing: `{material}`**

- If true: keep LIVE order caps / daily loss brakes; do not “fix” lag by loosening SMA buffers without a new Policy backtest.
- If false: lag still exists but may be smaller than fear — still size for the **worst** column, not the median.

Raw: `reports/improve/ae12-lag-mdd.json`
"""
    OUT_MD.write_text(md)
    print(json.dumps({k: payload[k] for k in (
        "n_switches", "lag_is_material_for_sizing", "risk_off_summary", "risk_on_summary"
    )}, ensure_ascii=False, indent=2))
    print(f"Wrote {OUT_JSON} and {OUT_MD}")


if __name__ == "__main__":
    main()
