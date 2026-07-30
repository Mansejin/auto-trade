# atr-v1 FAIL

- slug: `daytrade-edge-15m-div-atr-v1`
- hypothesis: BTC 15m hidden bull (price HL3 + RSI LL3) @ BB lower with ATR contracting (atr14 < atr offset 3) → long; exit BB upper only.
- hypers: tf=15m, div_lookback=3, atr_contract_lookback=3
- fail_mode: SPARSE_ZERO
- W1 2026-06-30~2026-07-29: return +0.00%, PF N/A, trades 0, trades/day 0.00, fees on
- W2 2026-05-31~2026-06-29: return +0.00%, PF N/A, trades 0, trades/day 0.00, fees on
- W3 2026-05-01~2026-05-30: return +0.00%, PF N/A, trades 0, trades/day 0.00, fees on
- bar A: FAIL (0/3 net>0 with PF≥1.2 or zero-loss)
- bar B: PASS (worst +0.00% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- ledger.next_priority: Encode daytrade-edge-15m-div-atr-v2: ONE ATR expanding gate (atr14 > atr offset 3) on hidden-bull v1 base @ BB lower → BB upper. No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 2767, warmup bars: 25)
Benchmark   +1.85%
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

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -17.47%
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
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -4.49%
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
