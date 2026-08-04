# AE4 — Bull participation beyond EMA (2026-07-28)

> Toolkit stdout only. Fees on. No slippage / book / partial fills.  
> **Not investment advice. Past ≠ future.**

## Hypothesis

Non-EMA bull engines (MACD / DI / Ichimoku / SMA / CCI / StochRSI / OBV) can close the
`2021-10-01`…`2021-12-03` participation gap vs B&H without wrecking Policy C 5y compound.

## Falsification criterion

Candidate fails if **Policy C 5y segment-chain compound ≤ bull-v2 baseline (+425.85%)**,
or Y3 mega-bull year collapses while only patching the single weak window.

## Spot windows (total return %)

| Family | 2021-10 bull seg | Y3 | Y4 |
|--------|-----------------:|---:|---:|
| **bull-v2 EMA5/20 (baseline)** | **-3.48** | **+136.75** | **+71.79** |
| SMA5/20 | +6.58 | +82.88 | +82.88 |
| SMA10/50 | **+33.12** | +119.24 | +30.45 |
| MACD 12/26/9 | +1.30 | +66.12 | +61.05 |
| CCI signal | +12.19 | +77.29 | +19.43 |
| OBV signal | +20.78 | +119.24 | +21.94 |
| Ichimoku TK+cloud | +2.17 | +29.01 | +35.02 |
| DI cross ADX20 | +1.33 | -27.76 | +17.51 |
| StochRSI+ADX/DI | +6.82 | +27.00 | +23.80 |

## Policy C 5y compound (bear=m5-v6, sideways=v5, bull/transition=candidate)

| Bull engine | Compound |
|-------------|----------:|
| **bull-v2 (keep)** | **+425.85%** |
| SMA5/20 | +330.59% |
| SMA10/50 | +264.26% |
| MACD | +246.20% |
| OBV | +179.78% |
| Ichimoku | +154.43% |
| StochRSI | +139.26% |
| CCI | +112.91% |

## Verdict

**Hypothesis FALSIFIED for promotion.** Several families fix 2021-10 locally (esp. SMA10/50, OBV),
but none beat bull-v2 on the full Policy C 5y chain. DI destroys Y3. Keep
`strategies/regime-bull-trend-4h-v2.json` for bull+transition.

Artifacts: `strategies/regime-bull-*-4h-v1.json`, `reports/five-year/ae4-bull-family-compare.json`,
`reports/five-year/policyC-5y-bull-*-path.json`.
