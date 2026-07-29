# Card: daytrade-bb-rsi-div-v3 (draft)

| Field | Value |
|-------|-------|
| Slug | `daytrade-bb-rsi-div-v3` |
| Market | KRW-BTC / 5m |
| Status | next (not frozen) |
| Hypers (≤3) | `rsi_reclaim=35`, `bb_std=2.0`, `rsi_exit=55` |
| Parent | `daytrade-bb-rsi-div-v2` (reject: all windows net≤0, trades/day≈2–3) |

## Hypothesis (one line)

BTC daytrade long-only: while close at/below BB lower, RSI reclaim above 35 (prior bar < 35), fade to BB mid or RSI≥55.

## Structural change vs v2

- Entry trigger: RSI one-bar reclaim (rsi>35 & rsi[1]<35) at/under BB lower — not band cross_above + RSI mid-cap + rising lookback.
- Drop RSI rising lookback and RSI<50 gate.
- Keep band outer stress (close ≤ lower) as location filter.

## Rules

- Buy: close ≤ BB lower AND RSI > 35 AND RSI[1] < 35.
- Sell: close ≥ BB mid OR RSI ≥ 55.
- Stop-loss 0.8% / take-profit 1.5%.
