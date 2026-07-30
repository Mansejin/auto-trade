# atr-v2 PASS

- slug: `daytrade-edge-15m-div-atr-v2`
- hypothesis: BTC 15m hidden bull (price HL3 + RSI LL3) @ BB lower with ATR expanding (atr14 > atr offset 3) → long; exit BB upper only.
- hypers: tf=15m, div_lookback=3, atr_expand_lookback=3
- fail_mode: PASS
- W1 2026-06-30~2026-07-29: return -0.21%, PF 0.00, trades 1, trades/day 0.03, fees on
- W2 2026-05-31~2026-06-29: return +0.39%, PF ∞, trades 1, trades/day 0.03, fees on
- W3 2026-05-01~2026-05-30: return +1.33%, PF ∞, trades 2, trades/day 0.07, fees on
- bar A: PASS (2/3: W2 +0.39% PF∞, W3 +1.33% PF∞; W1 net≤0)
- bar B: PASS (worst −0.21% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: skipped_no_deploy
- ledger.next_priority: Encode daytrade-edge-15m-div-atr-or-v1: ONE ATR expanding gate (atr14 > atr offset 3) on classic+hidden OR @ BB lower → BB upper. No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 2767, warmup bars: 25)
Benchmark   +1.85%
Total Return -0.21%
CAGR        -2.59%
MDD         -0.87%
Sharpe      -1.14  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  999
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -17.47%
Total Return +0.39%
CAGR        +4.96%
MDD         -0.73%
Sharpe      1.72  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,002
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -4.49%
Total Return +1.33%
CAGR        +18.11%
MDD         -0.50%
Sharpe      4.63  (Rf=0, portfolio / full equity curve)
Sharpe      30.98  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 2 / final_bar 0
Total Fees  2,008
```
