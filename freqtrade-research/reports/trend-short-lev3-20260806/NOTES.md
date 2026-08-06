# TrendShortV1 1x vs Lev3 — same SL/ROI profit ratios

Date: 2026-08-06
Config: `config.bitget-trend-short-lev-bt.json` (stake=100, orderbook off, fee 0.06%)
Windows (cpp-aligned): h1=2025-09-01→2026-02-04 · h2=2026-02-04→2026-08-05
SL/ROI unchanged: -3% / +9% on freqtrade `current_profit` (= price_move × leverage, fees in)

| | 1x h1 | 1x h2 | 3x h1 | 3x h2 |
|--|------:|------:|------:|------:|
| trades | 27 | 33 | 200 | 247 |
| abs USDT | +23.36 | +14.05 | -17.01 | -100.01 |
| profit % | +2.34 | +1.40 | -1.70 | -10.00 |
| PF | 1.44 | 1.20 | 0.96 | 0.84 |
| max DD % | 1.79 | 2.44 | 8.61 | 13.65 |
| market | -30.02% | -15.31% | (same) | (same) |

At 3x, same profit-ratio SL/TP ≈ **~1% price SL / ~3% price TP** → many more short stops, PF < 1 both halves.

Limitations: no slippage / order-book / partial fills.

LIVE: still 1x. Do not switch until SL/TP decision.
