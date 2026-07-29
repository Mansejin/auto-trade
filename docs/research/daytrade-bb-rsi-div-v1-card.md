# Card: daytrade-bb-rsi-div-v1 (draft)

| Field | Value |
|-------|-------|
| Slug | `daytrade-bb-rsi-div-v1` |
| Market | KRW-BTC / 5m |
| Status | testing (not frozen) |
| Hypers (≤3) | `rsi_os=30`, `bb_std=2.0`, `div_lookback=5` |

## Hypothesis (one line)

BTC daytrade: RSI extreme + BB outer band, divergence confirms fade to mid; SL beyond signal extreme.

## Rules

- Buy: close < BB lower AND RSI < 30 AND close < close[5] AND RSI > RSI[5] (bullish divergence proxy).
- Sell: close ≥ BB mid OR RSI ≥ 50.
- Stop-loss 0.8% / take-profit 1.5%.
- Indicators only: RSI, Bollinger Bands (divergence via price/RSI offset compare).

## Falsification

Promotion bar fails on 3×~30d windows (fee on, same encoding).
