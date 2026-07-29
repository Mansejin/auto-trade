# Card: daytrade-bb-rsi-div-v2 (draft)

| Field | Value |
|-------|-------|
| Slug | `daytrade-bb-rsi-div-v2` |
| Market | KRW-BTC / 5m |
| Status | next (not frozen) |
| Hypers (≤3) | `rsi_cap=50`, `bb_std=2.0`, `div_lookback=3` |
| Parent | `daytrade-bb-rsi-div-v1` (reject: sparse trades, all windows net≤0) |

## Hypothesis (one line)

BTC daytrade long-only: BB lower reclaim with RSI still below mid and RSI rising vs lookback (bullish momentum vs band stress), fade to BB mid.

## Structural change vs v1

- Entry: `cross_above` BB lower reclaim (not pierce+hold under band).
- Drop hard RSI oversold floor and price LL requirement.
- Keep RSI rising vs lookback as divergence/momentum proxy; RSI must still be < mid at entry.

## Rules

- Buy: close cross_above BB lower AND RSI < 50 AND RSI > RSI[3].
- Sell: close ≥ BB mid OR RSI ≥ 55.
- Stop-loss 0.8% / take-profit 1.5%.
