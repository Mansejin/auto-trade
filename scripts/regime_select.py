#!/usr/bin/env python3
"""Classify KRW-BTC daily regime (v2) and select a backtest strategy (no live trading).

v2 adds DI confirmation and SMA50 recovery filter so rising recoveries under a
bearish MA structure map to transition (trend/participation) instead of bear.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Policy C — evidence-weighted map on regime-v2 segments
POLICY_C = {
    "bull": "strategies/regime-bull-trend-4h-v2.json",
    "bear": "strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "strategies/regime-sideways-mr-4h-v5.json",
    "transition": "strategies/regime-bull-trend-4h-v2.json",
}


def fetch_days(market: str = "KRW-BTC", want: int = 260) -> list[dict]:
    rows: list[dict] = []
    to = None
    while len(rows) < want:
        url = f"https://api.upbit.com/v1/candles/days?market={market}&count=200"
        if to:
            url += f"&to={to}"
        req = urllib.request.Request(
            url, headers={"Accept": "application/json", "User-Agent": "regime-select-v2"}
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


def adx_last(highs, lows, closes, period: int = 14):
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
    return pdi[-1], mdi[-1], adx[-1]


def classify(candles: list[dict]) -> dict:
    closes = [c["trade_price"] for c in candles]
    highs = [c["high_price"] for c in candles]
    lows = [c["low_price"] for c in candles]
    i = len(closes) - 1
    s50 = sma(closes, 50, i)
    s200 = sma(closes, 200, i)
    pdi, mdi, adx = adx_last(highs, lows, closes)
    if None in (s50, s200, adx, pdi, mdi):
        raise RuntimeError("insufficient candles for SMA200/ADX/DI")
    # Regime engine v2
    if adx < 20:
        regime = "sideways"
    elif closes[i] > s200 and s50 > s200 and pdi >= mdi:
        regime = "bull"
    elif closes[i] < s200 and s50 < s200 and closes[i] < s50 and mdi > pdi:
        regime = "bear"
    else:
        regime = "transition"
    return {
        "date": candles[i]["candle_date_time_utc"][:10],
        "regime": regime,
        "close": closes[i],
        "sma50": s50,
        "sma200": s200,
        "adx": round(adx, 2),
        "pdi": round(pdi, 2),
        "mdi": round(mdi, 2),
        "selected_file": POLICY_C[regime],
        "policy": "C_regime_v2",
        "engine": "v2",
        "live_trading": False,
    }


def main() -> None:
    candles = fetch_days()
    result = classify(candles)
    out = ROOT / "reports" / "regime-current.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nSelected strategy file: {result['selected_file']}")
    print("Backtest-only selector. No live orders.")


if __name__ == "__main__":
    main()
