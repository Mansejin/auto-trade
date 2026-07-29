# AE9 — Trend pullback continuation 4h

> Family: **trend continuation** (not oversold bounce).  
> Distinct from Policy C bull-v2 (EMA5/20 cross): entry = close reclaim EMA20 while EMA20>EMA50, ADX≥25, +DI>-DI.  
> Params frozen before results. Not investment advice.

## Hypothesis

In an established uptrend (EMA20>EMA50, ADX≥25, +DI>-DI), when price **crosses back above EMA20**, the trend tends to continue enough to beat fees before EMA20 fails or −DI dominates.

## Falsification

Falsify if early/prior windows have **PF < 1** and non-positive (or clearly negative) total return.

## Results

| Window | Period | Total | B&H | MDD | PF | WR | n |
|--------|--------|------:|----:|----:|---:|---:|--:|
| Primary 6m | 2026-01-29→07-28 | +1.62% | −27.74% | −7.25% | 1.49 | 25% | 8 |
| Early OOS | 2025-07-29→2026-01-29 | **−1.26%** | −21.95% | −2.15% | **0.52** | 33% | 6 |
| Prior 6m | 2025-01-29→07-29 | **−3.93%** | +4.65% | −4.55% | **0.02** | 17% | 6 |

## Verdict

**FALSIFIED.** Primary only looks “ok vs crashing B&H”; earlier windows lose with PF≪1. Do not loosen ADX/DI filters to raise win rate.
