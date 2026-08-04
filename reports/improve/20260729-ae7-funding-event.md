# AE7 — Funding extreme → next-day KRW-BTC (event study)

> Alt-data alpha test **without** empty WS scaffold.  
> Binance futures API HTTP 451 here → **OKX** BTC-USDT-SWAP funding history as proxy.  
> Not investment advice. Fees/slippage not modeled.

## Hypothesis (pre-registered)

When perpetual `funding_rate <= -0.05%`, the **next UTC day** KRW-BTC close-to-close return has **higher mean** and **higher hit-rate** than the same-period daily baseline.

## Anti-overfit controls

- Threshold fixed at **-0.05%** (no sweep)
- Holdout frozen: event dates `>= 2026-01-01`
- No Strategy JSON / LIVE promote in this step

## Coverage

- Funding points: **273** (2026-04-29 → 2026-07-29)
- Events at threshold: **0**

## Results

| Set | Events n | Mean fwd 1d | Hit rate | Baseline mean | Baseline hit |
|-----|----------:|------------:|---------:|--------------:|-------------:|
| Train 2024–2025 | 0 | None% | None | 0.1306% | 0.5034 |
| Holdout 2026+ | 0 | None% | None | -0.1325% | 0.5 |

## Verdict

**FALSIFIED**

Reasons: holdout_n_too_small=0

Raw: `reports/improve/ae7-funding-event-study.json`
