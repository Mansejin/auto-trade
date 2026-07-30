# 10m-div-atr-adx-v1 PASS

- slug: `daytrade-edge-10m-div-atr-adx-v1`
- hypothesis: BTC 10m ADX<25 + ATR expand (atr>atr offset 3) + classic+hidden OR (HL/LL3 RSI) @ BB lower → long; exit BB upper only.
- hypers: tf=10m, adx_lt=25, atr_offset=3
- fail_mode: PASS
- W1 2026-06-30~2026-07-29: return +0.78%, PF 2.33, trades 3, trades/day 0.10, fees on
- W2 2026-05-31~2026-06-29: return +1.21%, PF ∞, trades 1, trades/day 0.03, fees on
- W3 2026-05-01~2026-05-30: return +0.29%, PF ∞, trades 1, trades/day 0.03, fees on
- bar A: PASS (3/3 net>0 with PF≥1.2 or zero-loss net>0)
- bar B: PASS (worst +0.29% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: skipped_no_deploy
- ledger.next_priority: Encode daytrade-edge-10m-div-atr-adx-hold-v1: atr-adx + take_profit null; exit BB upper only on 10m. No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 4149, warmup bars: 29)
Benchmark   +1.93%
Total Return +0.78%
CAGR        +10.31%
MDD         -0.95%
Sharpe      2.05  (Rf=0, portfolio / full equity curve)
Sharpe      15.41  (Rf=0, trades / position holding periods only)
Trades      3  Win Rate 67% (before fees)
Profit Factor  2.33 (before fees)
SL 1 / TP 0 / sell 2 / final_bar 0
Total Fees  3,029
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 4177, warmup bars: 29)
Benchmark   -17.76%
Total Return +1.21%
CAGR        +16.33%
MDD         -1.17%
Sharpe      3.53  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,006
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 4177, warmup bars: 29)
Benchmark   -4.49%
Total Return +0.29%
CAGR        +3.77%
MDD         -0.27%
Sharpe      2.97  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,001
```
