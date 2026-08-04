# 빗각 V1 day — volume-pivot channel (BTC 15m) — 2026-07-29

## Spec (frozen)

| Item | Value |
|------|-------|
| Pair | Bitget `BTC/USDT:USDT` only |
| TF | 15m (day trading; ~목표 3–4회/일) |
| Anchors | swing±3 + `vol >= 1.5 * SMA(vol,20)` |
| Channel | 저저고 (상승) / 고고저 (하락), lookback 192 |
| Mode | A only — rising→long lower; falling→short upper |
| Liquidity | 1d volume >= 0.75 × SMA20(day vol) else flat |
| Exit | mid rail signal / ROI +1% / SL −0.5% |
| Fee | 0.06% taker |
| Code | `DiagonalVolumePivotDayV1.py` |
| Config | `config.bitget-diagonal-day-v1.json` |

Hypothesis: volume-pivoted rails + day liquidity gate beat dead LR(40) proxies on BTC day TF.

## Results

| Window | Trades (avg/day) | Profit | PF | Market | Verdict |
|--------|------------------|--------|-----|--------|---------|
| W1 05-15→05-29 | 37 (2.64) | +0.42% | 1.06 | −9.5% | weak pass |
| W2 06-15→06-29 | 21 (1.5) | −1.28% | 0.79 | −9.5% | **fail** |
| W3 07-01→07-15 | 28 (2.0) | −3.74% | 0.60 | +10.7% | **fail** |

**Falsified** (≥2/3 windows PF&lt;1 and net&lt;0).

Notes:
- Frequency ~1.5–2.6/day — under the 3–4 wish, but not sparse.
- W1/W2: shorts helped, longs bled in down markets (Mode A still takes longs on any rising local channel).
- W3 up-market still lost both sides → rail geometry / touch rule not an edge under fees.

## Do not

- Retune `vol_k` / `touch_pct` / ROI after seeing these numbers.
- Promote to LIVE / SCALP sleeve.

## Next (pick one — new version letter)

1. **V2 Mode B**: same volume pivots, only break+retest (no first-touch MR).
2. **Regime gate**: only long when daily bull / only short when daily bear (still volume rails).
3. **Alert-only**: bot draws rails + pings; human confirms (matches discretionary 빗각).
4. **Stop day encoding**: keep CORE Policy C; treat short-TF 빗각 as non-automatable.
