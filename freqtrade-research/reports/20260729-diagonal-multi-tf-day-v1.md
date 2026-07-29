# 빗각 Multi-TF day — 4h rails / 15m entries (BTC) — 2026-07-29

## Spec (frozen)

| Item | Value |
|------|-------|
| Structure | 4h volume-pivot channel (lookback 60) |
| Entry TF | 15m Mode A soft-touch (0.25%) + trend candle |
| Extrapolation | rails slope forward between 4h closes |
| Liquidity | 1d vol ≥ 0.75×SMA20 |
| SL / ROI | −0.5% / +1% + exit at 4h mid |
| Code | `DiagonalMultiTfDayV1.py` |
| Config | `config.bitget-diagonal-mtf-v1.json` |

Hypothesis: discretionary multi-TF (draw high, enter low) beats same-TF V1.

## Results

| Window | Trades (avg/day) | Profit | PF | Market | Verdict |
|--------|------------------|--------|-----|--------|---------|
| W1 05-15→05-29 | 12 (0.86) | −1.74% | 0.61 | −9.5% | **fail** |
| W2 06-15→06-29 | 3 (0.21) | −0.97% | 0.20 | −9.5% | **fail** |
| W3 07-01→07-15 | 5 (0.36) | −1.48% | 0.40 | +10.7% | **fail** |

**Falsified** (3/3). Frequency far below day-trade target.

## Read

- Structure got cleaner (fewer trades) but **not more correct** under taker fees.
- 4h rails rarely visited on 15m in these windows → too sparse to learn from.
- Same Mode A “first touch MR” thesis as V1; only the drawing TF changed.

## Still worth trying (multi-TF family, not retune)

1. **1h→15m** — same idea, more rail visits (user-style often mixes 1h too).
2. **4h structure + Mode B continuation** — breakout/retest of 4h rail on 15m (proposal #2 on HTF rails).
3. **#4 filter** — keep another entry engine; 4h rail only as distance filter.

Do not widen touch% on this file after seeing results.
