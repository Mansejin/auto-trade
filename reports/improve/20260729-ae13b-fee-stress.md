# AE13b — Fee stress on AE13 H_rich fade (frozen)

> Same frozen rich cut (`premium >= 0.004563296109377913` from AE13 train 90th).  
> Same time holdout (last 30% of premium series).  
> Action assumed for costing: **short** next-day KRW-BTC (fade). Baseline = always-short in the same window.  
> **No cut refit. No LIVE promote.**

## Hypothesis (frozen before scoring)

On holdout days with Upbit BTC premium ≥ frozen rich cut, a 1-day fade (short) still beats always-short **after** primary round-trip costs.

## Primary gate

Round-trip **20 bps** (≈ Upbit 5+5 fee + ~10 slip). Survive if holdout **net fade mean > always-short baseline mean** and **fade directional hit (price down) > baseline down-hit**.

## Results

Holdout rich n=21. Gross fade mean %=0.6272, fade dir hit=0.6667.  
Baseline always-short mean %=0.1388, down hit=0.5068.

| RT bps | Net mean % | Net>0 hit | Fade dir hit | Base short mean | Base down hit | Survives |
|-------:|-----------:|----------:|-------------:|----------------:|--------------:|:--------:|
| 10 | 0.5272 | 0.6667 | 0.6667 | 0.1388 | 0.5068 | Y |
| 20 | 0.4272 | 0.6667 | 0.6667 | 0.1388 | 0.5068 | Y |
| 30 | 0.3272 | 0.6667 | 0.6667 | 0.1388 | 0.5068 | Y |
| 50 | 0.1272 | 0.4762 | 0.6667 | 0.1388 | 0.5068 | N |

## Verdict

**SURVIVES_PRIMARY_FEE**

Promotion: **No.** Optional human paper micro-size only if primary survives — still outside Policy C map. H2 OB study remains blocked until collect ≥336 rows.

Raw: `reports/improve/ae13b-fee-stress.json`
