# 10m-div-v1 PASS

- slug: `daytrade-edge-10m-div-v1`
- hypothesis: BTC 10m classic+hidden OR (HL/LL3 RSI) @ BB lower → long; exit BB upper only.
- hypers: tf=10m, div_lookback=3, bb_exit=upper
- fail_mode: PASS
- W1 2026-06-30~2026-07-29: return +0.99%, PF 2.84, trades 9, trades/day 0.30, fees on
- W2 2026-05-31~2026-06-29: return +2.63%, PF 2.97, trades 5, trades/day 0.17, fees on
- W3 2026-05-01~2026-05-30: return +0.05%, PF 1.44, trades 3, trades/day 0.10, fees on
- bar A: PASS (3/3 net>0 with PF≥1.2)
- bar B: PASS (worst +0.05% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: skipped_no_deploy
- ledger.next_priority: Encode daytrade-edge-10m-div-adx-v1: ADX<25 + classic+hidden OR @ BB lower → BB upper on 10m. No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 4149, warmup bars: 25)
Benchmark   +1.93%
Total Return +0.99%
CAGR        +13.18%
MDD         -1.59%
Sharpe      1.64  (Rf=0, portfolio / full equity curve)
Sharpe      14.04  (Rf=0, trades / position holding periods only)
Trades      9  Win Rate 56% (before fees)
Profit Factor  2.84 (before fees)
SL 1 / TP 0 / sell 8 / final_bar 0
Total Fees  9,085
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 4177, warmup bars: 25)
Benchmark   -17.76%
Total Return +2.63%
CAGR        +38.71%
MDD         -1.89%
Sharpe      3.63  (Rf=0, portfolio / full equity curve)
Sharpe      22.98  (Rf=0, trades / position holding periods only)
Trades      5  Win Rate 60% (before fees)
Profit Factor  2.97 (before fees)
SL 2 / TP 1 / sell 2 / final_bar 0
Total Fees  4,979
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
