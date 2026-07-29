#!/usr/bin/env python3
"""Regime engine v2: DI + SMA50 recovery filter (no live trading).

Fixes fake-bear rising windows (e.g. 2024-08..11 labeled bear while price rose)
by requiring close < SMA50 and -DI > +DI for bear.
"""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "regimes-krw-btc-1d-v2.json"
MIN_RUN = 14  # shorter than v1(21) to capture more sideways samples


def fetch_days(market: str = "KRW-BTC", want: int = 1100) -> list[dict]:
    rows: list[dict] = []
    to = None
    while len(rows) < want:
        url = f"https://api.upbit.com/v1/candles/days?market={market}&count=200"
        if to:
            url += f"&to={to}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "regime-engine-v2"},
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
    by = {c["candle_date_time_utc"][:10]: c for c in rows}
    return [by[k] for k in sorted(by)]


def sma(arr: list[float], p: int, i: int) -> float | None:
    if i + 1 < p:
        return None
    return sum(arr[i + 1 - p : i + 1]) / p


def series_adx(highs, lows, closes, period: int = 14):
    n = len(closes)
    tr = [None] * n
    plus_dm = [None] * n
    minus_dm = [None] * n
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        up = highs[i] - highs[i - 1]
        dn = lows[i - 1] - lows[i]
        plus_dm[i] = up if up > dn and up > 0 else 0.0
        minus_dm[i] = dn if dn > up and dn > 0 else 0.0

    def wilder(vals, p):
        out = [None] * n
        out[p] = sum(vals[1 : p + 1])
        for i in range(p + 1, n):
            out[i] = out[i - 1] - out[i - 1] / p + vals[i]
        return out

    atr = wilder(tr, period)
    pdm = wilder(plus_dm, period)
    mdm = wilder(minus_dm, period)
    pdi = [None] * n
    mdi = [None] * n
    dx = [None] * n
    adx = [None] * n
    for i in range(n):
        if atr[i] and atr[i] != 0 and pdm[i] is not None:
            pdi[i] = 100 * pdm[i] / atr[i]
            mdi[i] = 100 * mdm[i] / atr[i]
            denom = pdi[i] + mdi[i]
            dx[i] = 100 * abs(pdi[i] - mdi[i]) / denom if denom else 0.0
    start = period * 2
    adx[start] = sum(dx[i] for i in range(period, start + 1)) / period
    for i in range(start + 1, n):
        adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period
    return pdi, mdi, adx


def classify_day(close, s50, s200, adx, pdi, mdi) -> str:
    if None in (s50, s200, adx, pdi, mdi):
        return "warmup"
    if adx < 20:
        return "sideways"
    # bull: structure + DI confirmation
    if close > s200 and s50 > s200 and pdi >= mdi:
        return "bull"
    # bear: below both MAs AND still below SMA50 (not recovering) AND -DI dominant
    if close < s200 and s50 < s200 and close < s50 and mdi > pdi:
        return "bear"
    return "transition"


def build_segments(
    candles: list[dict], min_run: int = MIN_RUN
) -> tuple[list[dict], dict]:
    closes = [c["trade_price"] for c in candles]
    highs = [c["high_price"] for c in candles]
    lows = [c["low_price"] for c in candles]
    dates = [c["candle_date_time_utc"][:10] for c in candles]
    pdi, mdi, adx = series_adx(highs, lows, closes)

    labels = []
    for i in range(len(closes)):
        s50 = sma(closes, 50, i)
        s200 = sma(closes, 200, i)
        labels.append(classify_day(closes[i], s50, s200, adx[i], pdi[i], mdi[i]))

    raw = []
    cur = None
    for i, lab in enumerate(labels):
        if lab == "warmup":
            continue
        if cur is None or lab != cur["regime"]:
            if cur:
                raw.append(cur)
            cur = {"start": dates[i], "end": dates[i], "regime": lab, "i0": i, "i1": i}
        else:
            cur["end"] = dates[i]
            cur["i1"] = i
    if cur:
        raw.append(cur)

    merged: list[dict] = []
    for s in raw:
        s["days"] = s["i1"] - s["i0"] + 1
        if merged and s["days"] < min_run:
            prev = merged[-1]
            prev["end"] = s["end"]
            prev["i1"] = s["i1"]
            prev["days"] = prev["i1"] - prev["i0"] + 1
        elif merged and merged[-1]["regime"] == s["regime"]:
            prev = merged[-1]
            prev["end"] = s["end"]
            prev["i1"] = s["i1"]
            prev["days"] = prev["i1"] - prev["i0"] + 1
        else:
            merged.append(dict(s))

    segs = []
    for s in merged:
        i0, i1 = s["i0"], s["i1"]
        segs.append(
            {
                "start": s["start"],
                "end": s["end"],
                "regime": s["regime"],
                "days": s["days"],
                "ret_pct": round((closes[i1] / closes[i0] - 1) * 100, 2),
            }
        )

    # Prefer last closed daily bar for "current" (Upbit includes a forming candle).
    i = len(closes) - 1
    if i >= 1:
        i = i - 1
    current = {
        "date": dates[i],
        "regime": labels[i],
        "close": closes[i],
        "sma50": sma(closes, 50, i),
        "sma200": sma(closes, 200, i),
        "adx": round(adx[i], 2) if adx[i] is not None else None,
        "pdi": round(pdi[i], 2) if pdi[i] is not None else None,
        "mdi": round(mdi[i], 2) if mdi[i] is not None else None,
        "bar": "closed",
    }
    return segs, current


def main() -> None:
    candles = fetch_days()
    segs, current = build_segments(candles)
    payload = {
        "method": {
            "version": "v2",
            "tf": "1d",
            "indicators": ["ADX14", "SMA50", "SMA200", "DI+/DI-"],
            "rules": {
                "sideways": "ADX<20",
                "bull": "ADX>=20 & close>SMA200 & SMA50>SMA200 & +DI>=-DI",
                "bear": "ADX>=20 & close<SMA200 & SMA50<SMA200 & close<SMA50 & -DI>+DI",
                "transition": "else (includes recovery: close>SMA50 while structure still bearish)",
                "min_run_days": MIN_RUN,
            },
            "note": "v2 splits fake-bear rising recoveries into transition/sideways",
        },
        "range": {
            "from": candles[0]["candle_date_time_utc"][:10],
            "to": candles[-1]["candle_date_time_utc"][:10],
            "n": len(candles),
        },
        "segments": segs,
        "current": current,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
