# AE8 — Disparity stretch fade 1h (orthogonal to AE6)

> Different TF (1h) and indicator family (disparity) vs AE6 MFI/Williams.  
> **No** AE6 parameter recycling. Thresholds pre-set: `disp_20 < 97`, ADX≥15, SL2.5/TP4.  
> Not investment advice.

## Hypothesis

When 1h `disp_20 < 97` and ADX≥15, price is stretched below its MA20 and a short-term rebound toward `disp_20 ≥ 100` occurs more often than continued dump.

## Falsification

Falsify if early/prior windows show **PF < 1** and **total return ≤ 0** (or large absolute loss), even if the latest window looks good.

## Results

| Window | Period | Total | B&H | MDD | PF | WR | n |
|--------|--------|------:|----:|----:|---:|---:|--:|
| Primary (latest 3m) | 2026-04-29→07-28 | **+5.19%** | −18.56% | −2.88% | 3.27 | 80% | 5 |
| Early OOS | 2026-01-29→04-29 | **−12.65%** | −11.65% | −17.28% | **0.51** | 33% | 15 |
| Prior 3m | 2025-10-29→2026-01-29 | −0.24% | −23.30% | −5.17% | 1.07 | 60% | 10 |

## Verdict

**FALSIFIED as standalone alpha.**

Latest window is a classic **in-sample trap** (sparse n=5, strong PF). The immediately preceding window loses hard (PF 0.51). Do **not** tighten/loosen `97` to rescue primary.

## Closed this session

| id | Verdict |
|----|---------|
| AE6 | Falsified standalone |
| AE6b | Falsified (sparse + deep-bear PF 0.13) |
| AE7 | Untestable at −0.05% with public history depth |
| AE7b | Falsified (holdout mean ≤ baseline) |
| AE8 | Falsified (early OOS collapse) |

## Next (AE9+)

Prefer ideas that are **not** “another oversold bounce”:
- Forward-collect funding/orderbook for a pre-registered event study with longer history
- Or a **trend-continuation** hypothesis with frozen holdout (opposite family from mean-reversion scrapes)
