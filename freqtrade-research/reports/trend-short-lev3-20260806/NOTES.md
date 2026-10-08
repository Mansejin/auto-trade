# TrendShortV1 1x vs Lev3 — aligned windows

Date: 2026-08-06
Config base: `config.bitget-trend-short-lev-bt.json` (stake=100, orderbook off, fee 0.06%)
Windows (cpp-aligned): h1=2025-09-01→2026-02-04 · h2=2026-02-04→2026-08-05

freqtrade `current_profit` ≈ price_move × leverage (fees in).

## A) Same profit-ratio exits (SL -3% / ROI +9% @ any lev)

| | 1x h1 | 1x h2 | 3x h1 | 3x h2 |
|--|------:|------:|------:|------:|
| trades | 27 | 33 | 200 | 247 |
| abs USDT | +23.36 | +14.05 | -17.01 | -100.01 |
| profit % | +2.34 | +1.40 | -1.70 | -10.00 |
| PF | 1.44 | 1.20 | 0.96 | 0.84 |
| max DD % | 1.79 | 2.44 | 8.61 | 13.65 |

At 3x this ≈ ~1% price SL / ~3% price TP → overtrading, PF < 1.

## B) Price-matched exits @ 3x (SL -9% / ROI +27% profit ratio ≈ 3%/9% price)

Strategy: `TrendShortV1Lev3Px` + `config.bitget-trend-short-lev3px-bt.json`

| | 1x h1 | 1x h2 | 3x-px h1 | 3x-px h2 |
|--|------:|------:|------:|------:|
| trades | 27 | 33 | 27 | 33 |
| abs USDT | +23.36 | +14.05 | +75.05 | +38.42 |
| profit % | +2.34 | +1.40 | +7.51 | +3.84 |
| PF | 1.44 | 1.20 | 1.45 | 1.18 |
| max DD % | 1.79 | 2.44 | 5.49 | 7.33 |

Trade count matches 1x. Wallet % ≈ ~3× 1x; DD also higher. h2 PF 1.18 is slightly below the old ≥1.20 bar.

Limitations: no slippage / book / partial fills. LIVE still 1x until explicit switch.
