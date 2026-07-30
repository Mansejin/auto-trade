# short-v1 FAIL

- slug: `daytrade-edge-15m-div-short-v1`
- hypothesis: BTC 15m short-proxy: (classic bear HH+RSI LH3 OR hidden bear LH+RSI HH3) @ BB upper → buy; exit BB lower only.
- hypers: tf=15m, div_lookback=3, side=short-proxy
- fail_mode: WORST_BLEED
- W1 2026-06-30~2026-07-29: return -4.74%, PF 0.18, trades 9, trades/day 0.3, fees on
- W2 2026-05-31~2026-06-29: return -0.12%, PF 1.10, trades 2, trades/day 0.07, fees on
- W3 2026-05-01~2026-05-30: return -0.34%, PF 1.04, trades 4, trades/day 0.13, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (worst -4.74% < −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- ledger.next_priority: Encode daytrade-edge-15m-div-short-inv-v1: same classic+hidden bear @ BB upper, exit BB lower, inverted SL/TP 2.5/0.8. No deploy. Keep v1–v3 frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 2767, warmup bars: 25)
Benchmark   +1.85%
Total Return -4.74%
CAGR        -45.70%
MDD         -5.21%
Sharpe      -6.13  (Rf=0, portfolio / full equity curve)
Sharpe      -24.93  (Rf=0, trades / position holding periods only)
Trades      9  Win Rate 22% (before fees)
Profit Factor  0.18 (before fees)
SL 6 / TP 0 / sell 3 / final_bar 0
Total Fees  8,764
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -17.47%
Total Return -0.12%
CAGR        -1.47%
MDD         -1.47%
Sharpe      -0.31  (Rf=0, portfolio / full equity curve)
Sharpe      1.15  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 50% (before fees)
Profit Factor  1.10 (before fees)
SL 1 / TP 0 / sell 1 / final_bar 0
Total Fees  2,007
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -4.49%
Total Return -0.34%
CAGR        -4.25%
MDD         -2.54%
Sharpe      -0.46  (Rf=0, portfolio / full equity curve)
Sharpe      0.53  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 25% (before fees)
Profit Factor  1.04 (before fees)
SL 1 / TP 0 / sell 3 / final_bar 0
Total Fees  4,025
```
