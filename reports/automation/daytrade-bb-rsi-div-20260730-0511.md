# 1h-div-v1 FAIL

- slug: `daytrade-edge-1h-div-v1`
- hypothesis: BTC 1h classic+hidden OR (HL/LL3 RSI) @ BB lower → long; exit BB upper only. (20m unavailable in toolkit enum.)
- hypers: tf=1h, div_lookback=3, bb=20x2
- fail_mode: A_FAIL
- W1 2026-06-30~2026-07-29: return +1.54%, PF ∞, trades 1, trades/day 0.03, fees on
- W2 2026-05-31~2026-06-29: return +0.00%, PF N/A, trades 0, trades/day 0.00, fees on
- W3 2026-05-01~2026-05-30: return -0.90%, PF 0.00, trades 1, trades/day 0.03, fees on
- bar A: FAIL (1/3; only W1 net>0 with PF∞; W2 0 trades net0; W3 −0.90% PF0)
- bar B: PASS (worst −0.90% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- ledger.next_priority: Encode daytrade-edge-10m-div-mfi-v1: 10m MFI<20 + classic+hidden OR @ BB lower → upper only (flow gate on densest PASS line). No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 694, warmup bars: 25)
Benchmark   +2.21%
Total Return +1.54%
CAGR        +21.24%
MDD         -1.02%
Sharpe      3.24  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,008
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 697, warmup bars: 25)
Benchmark   -17.60%
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
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 697, warmup bars: 25)
Benchmark   -4.38%
Total Return -0.90%
CAGR        -10.75%
MDD         -0.90%
Sharpe      -4.96  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 1 / TP 0 / sell 0 / final_bar 0
Total Fees  996
```
