# atr-adx-v1 PASS

- slug: `daytrade-edge-15m-div-atr-adx-v1`
- hypothesis: BTC 15m classic+hidden OR (HL/LL3 RSI) @ BB lower with ADX<25 and ATR expanding (atr14 > atr offset 3) → long; exit BB upper only.
- hypers: tf=15m, atr_expand_lookback=3, adx_max=25
- fail_mode: PASS
- W1 2026-06-30~2026-07-29: return -0.04%, PF 1.20, trades 2, trades/day 0.07, fees on
- W2 2026-05-31~2026-06-29: return +1.30%, PF ∞, trades 1, trades/day 0.03, fees on
- W3 2026-05-01~2026-05-30: return +1.33%, PF ∞, trades 2, trades/day 0.07, fees on
- bar A: PASS (2/3: W2 +1.30% PF∞, W3 +1.33% PF∞; W1 net≤0)
- bar B: PASS (worst −0.04% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: skipped_no_deploy
- ledger.next_priority: Encode daytrade-edge-15m-div-atr-adx-hold-v1: ADX<25 + ATR expand + classic+hidden OR @ BB lower → BB upper with take_profit null. No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 2767, warmup bars: 29)
Benchmark   +1.85%
Total Return -0.04%
CAGR        -0.46%
MDD         -1.08%
Sharpe      -0.12  (Rf=0, portfolio / full equity curve)
Sharpe      4.83  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 50% (before fees)
Profit Factor  1.20 (before fees)
SL 1 / TP 0 / sell 1 / final_bar 0
Total Fees  2,009
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 2785, warmup bars: 29)
Benchmark   -17.47%
Total Return +1.30%
CAGR        +17.64%
MDD         -0.05%
Sharpe      5.97  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,006
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 2785, warmup bars: 29)
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
