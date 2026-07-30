# 30m-div-v1 FAIL

- slug: `daytrade-edge-30m-div-v1`
- hypothesis: BTC 30m classic+hidden OR (HL/LL3 RSI) @ BB lower → long; exit BB upper only (no ADX).
- hypers: tf=30m, div_lookback=3, bb_exit=upper
- fail_mode: A_FAIL
- W1 2026-06-30~2026-07-29: return -0.53%, PF 0.59, trades 2, trades/day 0.07, fees on
- W2 2026-05-31~2026-06-29: return +0.00%, PF N/A, trades 0, trades/day 0.00, fees on
- W3 2026-05-01~2026-05-30: return +1.63%, PF ∞, trades 2, trades/day 0.07, fees on
- bar A: FAIL (1/3 net>0 with PF≥1.2 or zero-loss)
- bar B: PASS (worst −0.53% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- ledger.next_priority: Encode daytrade-edge-10m-div-v1: classic+hidden OR @ BB lower → BB upper on 10m. No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 1385, warmup bars: 25)
Benchmark   +2.16%
Total Return -0.53%
CAGR        -6.46%
MDD         -1.38%
Sharpe      -1.40  (Rf=0, portfolio / full equity curve)
Sharpe      -6.65  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 50% (before fees)
Profit Factor  0.59 (before fees)
SL 1 / TP 0 / sell 1 / final_bar 0
Total Fees  2,001
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 1393, warmup bars: 25)
Benchmark   -18.03%
Total Return +0.00%
CAGR        +0.00%
MDD         0.00%
Sharpe      0.00  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      0  Win Rate N/A (0 executed trades) (before fees)
Profit Factor  N/A (0 executed trades) (before fees)
SL 0 / TP 0 / sell 0 / final_bar 0
Total Fees  0
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 1393, warmup bars: 25)
Benchmark   -4.52%
Total Return +1.63%
CAGR        +22.54%
MDD         -1.02%
Sharpe      2.88  (Rf=0, portfolio / full equity curve)
Sharpe      22.77  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 2 / final_bar 0
Total Fees  2,022
```
