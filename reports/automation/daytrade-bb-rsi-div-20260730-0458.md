# 10m-div-atr-v1 PASS

- slug: `daytrade-edge-10m-div-atr-v1`
- hypothesis: BTC 10m ATR expand (atr>atr offset 3) + classic+hidden OR (HL/LL3 RSI) @ BB lower → long; exit BB upper only.
- hypers: tf=10m, atr_offset=3, div_lookback=3, bb_exit=upper
- fail_mode: PASS
- W1 2026-06-30~2026-07-29: return +0.29%, PF 1.69, trades 9, trades/day 0.30, fees on
- W2 2026-05-31~2026-06-29: return +1.78%, PF 2.37, trades 4, trades/day 0.13, fees on
- W3 2026-05-01~2026-05-30: return +0.05%, PF 1.44, trades 3, trades/day 0.10, fees on
- bar A: PASS (3/3 net>0 with PF≥1.2)
- bar B: PASS (worst +0.05% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: skipped_no_deploy
- ledger.next_priority: Encode daytrade-edge-10m-div-atr-adx-v1: ADX<25 + ATR expand (atr>atr offset 3) + classic+hidden OR @ BB lower → BB upper on 10m. No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 4149, warmup bars: 25)
Benchmark   +1.93%
Total Return +0.29%
CAGR        +3.74%
MDD         -1.79%
Sharpe      0.53  (Rf=0, portfolio / full equity curve)
Sharpe      8.17  (Rf=0, trades / position holding periods only)
Trades      9  Win Rate 56% (before fees)
Profit Factor  1.69 (before fees)
SL 2 / TP 0 / sell 7 / final_bar 0
Total Fees  9,074
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 4177, warmup bars: 25)
Benchmark   -17.76%
Total Return +1.78%
CAGR        +24.86%
MDD         -2.41%
Sharpe      2.55  (Rf=0, portfolio / full equity curve)
Sharpe      19.06  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 50% (before fees)
Profit Factor  2.37 (before fees)
SL 2 / TP 1 / sell 1 / final_bar 0
Total Fees  3,976
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 4177, warmup bars: 25)
Benchmark   -4.49%
Total Return +0.05%
CAGR        +0.63%
MDD         -1.16%
Sharpe      0.23  (Rf=0, portfolio / full equity curve)
Sharpe      6.86  (Rf=0, trades / position holding periods only)
Trades      3  Win Rate 67% (before fees)
Profit Factor  1.44 (before fees)
SL 1 / TP 0 / sell 2 / final_bar 0
Total Fees  2,985
```
