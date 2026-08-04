# Regime-gate vs unfiltered — Bitget BTCUSDT-M RSI-BB scalp

Date: 2026-07-29  
Gate (frozen Policy-C style, Binance 1d SMA50/200+ADX, prior closed day):
- bull → long only
- bear → short only
- sideways / transition → no new entries

Entry/exit same as v4 (RSI+BB+ADX, ROI 0.8% / SL 0.3%, fee 0.06%).

## Comparison

| Window | Mode | Trades | L/S | Profit % | PF | Note |
|---|---|---|---|---|---|---|
| 05-15~29 | OFF | 19 | 8/11 | -0.68% | 0.87 | |
| 05-15~29 | ON | 2 | 0/2 | -0.83% | 0.00 | mostly transition; 2 short SL |
| 06-15~29 | OFF | 24 | 12/12 | -5.03% | 0.39 | |
| 06-15~29 | ON | 12 | 0/12 | -2.54% | 0.38 | bear→short only; loss halved, PF flat |
| 07-15~29 | OFF | 21 | 11/10 | -1.90% | 0.69 | |
| 07-15~29 | ON | 0 | 0/0 | 0% | N/A | almost all transition/sideways |

## Regime occupancy (gated calendar days)
- May window: mostly **transition**, few bear days
- June window: nearly all **bear**
- July window: **transition/sideways** dominant (bear only ~Jul 17)

## Hypothesis verdict
"Regime long/short bias improves WR/PF vs unfiltered in ≥2/3 windows"

→ **falsified / inconclusive**
- May: worse (PF 0)
- June: absolute loss improved, PF not
- July: 0 trades (sample insufficient)

Strict no-trade on transition/sideways kills activity in the scalp windows tested.
Research retain option (not promote): soften gate — e.g. sideways allow both, transition allow short-only — as a **new** frozen rule set (v2), not retuned on these results alone.

## Caveat
Daily regime labels use **Binance** BTCUSDT-M 1d (Bitget 1d history too short for SMA200). 5m fills still Bitget.
