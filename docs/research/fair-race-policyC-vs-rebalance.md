# Fair race: Policy C vs rebalance vs BTC hold (5y lump sum)

> Window aligned to five-year report: **2021-07-27 → 2026-07-26**  
> Mode: **lump sum 10M KRW, no monthly DCA** (so cash-sleeve rebalance can face trading strategies).  
> **Not investment advice.**

## Headline

| ID | Strategy | Return | Multiple | MDD | Notes |
|----|----------|-------:|---------:|----:|-------|
| **A** | Policy C segment chain (bull-v2 / m5-v6 / sw-v5) | **+425.9%** | **5.26×** | **−15.4%*** | *segment-end marks only |
| B | 50:50 ±12%p cd30 rebalance | +77.4% | 1.77× | −45.3% | daily equity |
| C2 | 70:30 ±10%p cd14 | +104.8% | 2.05× | −58.5% | daily equity |
| C | 80:20 ±10%p cd14 | +105.3% | 2.05× | −65.8% | daily equity |
| D | 100% BTC hold | +109.3% | 2.09× | −74.1% | daily equity |

Source JSON: `reports/bt-fair-race-policyC-vs-rebalance-5y.json`  
Policy C path: `reports/five-year/policyC-5y-v2bull-v5sw-path.json`

## Reading

1. **On this methodology, Policy C crushes simple allocation** on return (~4× the BTC hold multiple).
2. **MDD is not comparable**: A’s −15% ignores drawdowns *inside* each regime segment. B–D use true daily equity. Real Policy C continuous MDD is almost certainly deeper than −15%.
3. Among **honest daily-equity** sleeves, 50:50 is the risk cut; 80:20 ≈ BTC hold on return with slightly milder MDD; neither approaches Policy C’s *reported* compound.
4. Caveats that inflate A: full redeploy each segment, no switch friction, no idle cash between signals, toolkit fills next-bar, no slippage.

## Verdict (falsification-first)

| Question | Answer |
|----------|--------|
| Do the hard-built CORE strategies beat 50:50 / 80:20 rebalance on 5y segment-chain return? | **Yes, by a wide margin — under current Policy C accounting.** |
| Is that enough to retire rebalance as a benchmark? | **Not yet** — need continuous multi-strategy equity (or paper LIVE) for fair MDD / path dependency. |
| Is daytrade-edge pack in this race? | **No** — satellite; not in Policy C map. |

## Next proof (if pursued)

Rebuild one continuous equity curve: each day hold the active Policy C strategy’s mark (or flat cash when flat), then recompute MDD vs B/C/D on the same daily series.
