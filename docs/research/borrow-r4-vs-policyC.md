# Borrow R1–R4 (Trend×Vol) vs Policy C

Source idea: [quantsarahz/btcusdt-regime-multistrategy-trading](https://github.com/quantsarahz/btcusdt-regime-multistrategy-trading) R1–R4 grid (Trend/Range × Low/High vol). Repo blends weights and sets R4=0; we hard-switch onto our sleeves (Upbit one `STRATEGY_PATH`).

Script: `scripts/bt_borrow_r4_vs_policyC.py`  
Artifact: `reports/bt-borrow-r4-vs-policyC-20260731_070554.json`

## Frozen borrow map

| Cell | Classifier | Sleeve |
|------|------------|--------|
| R1 | Trend + LowVol | bull-v2 |
| R2 | Trend + HighVol | bull-v2 |
| R3 | Range + LowVol | sideways-mr-4h-v5 |
| R4 | Range + HighVol | cash-flat (key borrow: sit out) |

Classifier: ADX≥25 → trend else range; HighVol = ATR14 > SMA20(ATR); min_run=3 days.

Policy C unchanged: bull/transition→bull-v2, bear→m5-v6, sideways→sideways-v5.

## Race

| Window | Policy C | R4 borrow | B&H |
|--------|---------:|----------:|----:|
| in-sample 2021-07-27→2026-07-26 | **+425.9%** / MDD **−32.2%** | +269.1% / −45.6% | +109% / −74% |
| OOS 2018-04-12→2021-07-24 | **+387.4%** / MDD **−36.7%** | +18.0% / −36.7% | +394% / −67% |

## Verdict

**FALSIFIED_VS_POLICY_C.** R4 borrow loses return on both windows (−157%p / −369%p) and does not improve MDD (worse in-sample, ~flat OOS). Cash-on-R4 sits out chop that Policy C’s bear sleeve (m5-v6) still trades; segment churn is also higher (99 vs 36 in-sample).

No LIVE mount. CORE stays Policy C.
