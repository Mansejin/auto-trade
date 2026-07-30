# Fair race: Policy C vs rebalance vs BTC hold (5y lump sum)

> Window: **2021-07-27 → 2026-07-26** · Lump sum **10M KRW** · **no DCA**  
> **Not investment advice.**

## Continuous equity (this step)

Policy C daily curve rebuilt from **36 segment toolkit BTs** (trades marked on daily closes, path returns preserved).  
Artifact: `reports/bt-fair-race-continuous-20260730_121105.json`

| ID | Strategy | Return | Multiple | MDD (daily) |
|----|----------|-------:|---------:|------------:|
| **A** | **Policy C continuous** | **+425.8%** | **5.26×** | **−32.2%** |
| B | 50:50 ±12%p cd30 | +77.4% | 1.77× | −45.3% |
| C | 80:20 ±10%p cd14 | +105.3% | 2.05× | −65.8% |
| D | 100% BTC hold | +109.3% | 2.09× | −74.1% |

Prior soft MDD (segment-end marks only): **−15.4%** → continuous **−32.2%** (more honest, still best in race).

## Verdict

| Question | Answer |
|----------|--------|
| Does Policy C beat rebalance/hold on **return**? | **Yes** (~4× BTC hold multiple). |
| Does it also win on **daily MDD**? | **Yes** (−32% vs −45/−66/−74). |
| Still caveats? | Switch friction, slippage, fill assumptions; daytrade-edge pack not in this map. |

## Method notes

- Script: `scripts/bt_policyC_continuous_equity.py`
- Map: bull/transition → `regime-bull-trend-4h-v2`, bear → `m5-v6`, sideways → `regime-sideways-mr-4h-v5`
- Intra-trade marks use daily KRW-BTC closes; segment endpoints scaled to frozen path `ret` so compound matches `+425.85%`
