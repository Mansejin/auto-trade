# 30m-atr-adx-v1 FAIL

- slug: `daytrade-edge-30m-div-atr-adx-v1`
- hypothesis: BTC 30m classic+hidden OR (HL/LL3 RSI) @ BB lower with ADX<25 and ATR expanding (atr14 > atr offset 3) → long; exit BB upper only.
- hypers: tf=30m, atr_expand_lookback=3, adx_max=25
- fail_mode: SPARSE_ZERO
- W1 2026-06-30~2026-07-29: return -0.90%, PF 0.00, trades 1, trades/day 0.03, fees on
- W2 2026-05-31~2026-06-29: return +0.00%, PF N/A, trades 0, trades/day 0.00, fees on
- W3 2026-05-01~2026-05-30: return +0.00%, PF N/A, trades 0, trades/day 0.00, fees on
- bar A: FAIL (0/3 net>0)
- bar B: PASS (worst −0.90% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- ledger.next_priority: Encode daytrade-edge-30m-div-adx-v1: ADX<25 + classic+hidden OR @ BB lower → BB upper on 30m (drop ATR). No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 1385, warmup bars: 29)
Benchmark   +2.16%
Total Return -0.90%
CAGR        -10.75%
MDD         -1.38%
Sharpe      -3.56  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 1 / TP 0 / sell 0 / final_bar 0
Total Fees  995
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 1393, warmup bars: 29)
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
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 1393, warmup bars: 29)
Benchmark   -4.52%
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
