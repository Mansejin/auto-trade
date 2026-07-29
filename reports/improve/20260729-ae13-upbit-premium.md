# AE13 — Upbit internal BTC premium (orthogonal alt-data)

> Premium = `KRW-BTC / (USDT-BTC × KRW-USDT) − 1`.  
> Train (70%) fits rich/cheap percentiles; holdout scores once.  
> Not investment advice. **No LIVE / Policy C promote.**

## Hypotheses (frozen)

1. **H_rich:** premium ≥ train 90th (= `0.004563`) → next-day KRW-BTC **underperforms** baseline  
2. **H_cheap:** premium ≤ train 10th (= `-0.003981`) → next-day KRW-BTC **outperforms** baseline  

Overlap days: 783. Series n=782. Holdout days=235.

### H_rich fade — **RETAINED_for_research**


n=21 mean%=-0.6349 hit=0.3333 | baseline mean%=-0.1395 hit=0.4932

### H_cheap bounce — **FALSIFIED**

Reasons: `holdout_mean<=baseline_mean`, `holdout_hit<=baseline_hit`

n=43 mean%=-0.3059 hit=0.4419 | baseline mean%=-0.1447 hit=0.4953


## Overall

**PARTIAL_RETAIN**

Promotion: **No.**

Raw: `reports/improve/ae13-upbit-premium.json`
