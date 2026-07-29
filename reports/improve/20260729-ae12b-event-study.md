# AE12b — Frozen funding / orderbook event study

> Thresholds and holdout rule frozen at AE12 declaration.  
> H1 uses **HTX** historical funding (deep history). H2 needs forward Upbit orderbook JSONL.  
> Not investment advice. Fees/slippage not modeled.

## Hypotheses (frozen)

1. **H1:** `fundingRate <= -0.0002` → next UTC day KRW-BTC mean & hit-rate > same-window baseline  
2. **H2:** `|orderbook imbalance| >= 0.4` → next 1h move in imbalance direction beats hit-rate 0.5  

Holdout: last **30%** of events by time. Min holdout events: **8**.

### H1 Funding — **RETAINED_for_research**


| Set | n | Mean % | Hit | Baseline mean | Baseline hit |
|-----|--:|-------:|----:|--------------:|-------------:|
| Train | 103 | 0.7892 | 0.6019 | 0.1727 | 0.5097 |
| Holdout | 45 | 0.3886 | 0.6444 | -0.0633 | 0.4908 |

### H2 Orderbook — **NOT_READY**

Reason: `insufficient_forward_orderbook_rows`


## Interpretation

- **H1 retained for research only** — holdout mean (+0.39%) and hit (64%) beat same-window baseline (−0.06% / 49%). Not a LIVE signal: fees/slippage unmodeled; source is **HTX** history (not the OKX forward log).
- **Do not** sweep a new funding threshold or promote into Policy C from this pass.
- **H2** waits on VPS/cron `ae12_forward_collect.py` (≥336 orderbook rows). Re-run the same script; do not change `|imbalance|>=0.4`.

## Promotion

**No.** AE12b does not change Policy C or LIVE `STRATEGY_PATH`.

Raw: `reports/improve/ae12b-event-study.json`
