# AE7b — Relative funding extreme (train percentile)

AE7 (`funding <= -0.05%`) had **0 events** in available OKX/Bitget history (min ≈ -0.000085).  
AE7b tests a **pre-registered relative** rule instead of mining a new absolute cut.

## Hypothesis

Funding in the **bottom 10% of train-period funding** predicts next-day KRW-BTC outperformance vs baseline.

## Design (anti-overfit)

- Split funding series at midpoint time → train / holdout
- Threshold = 10th percentile of **train funding only** (= `-4.28255342382e-05`)
- Score holdout events on forward returns vs holdout daily baseline
- No return-based threshold search

## Results

| Set | Events | Mean fwd | Hit | Baseline mean | Baseline hit |
|-----|--------:|---------:|----:|--------------:|-------------:|
| Train | 13 | -0.024% | 0.4615 | -0.2709% | 0.5106 |
| Holdout | 8 | -0.1901% | 0.5 | -0.1334% | 0.4783 |

## Verdict

**FALSIFIED** — holdout_mean_fwd<=baseline_mean

Raw: `reports/improve/ae7b-funding-percentile-study.json`
