# short-inv-v1 FAIL

- slug: `daytrade-edge-15m-div-short-inv-v1`
- hypothesis: BTC 15m short-proxy inv: (classic bear HH+RSI LH3 OR hidden bear LH+RSI HH3) @ BB upper → buy; exit BB lower; SL 2.5 / TP 0.8.
- hypers: tf=15m, div_lookback=3, sl_tp=2.5/0.8
- fail_mode: WORST_BLEED
- W1 2026-06-30~2026-07-29: return -3.50%, PF 0.48, trades 10, trades/day 0.33, fees on
- W2 2026-05-31~2026-06-29: return -1.12%, PF 0.46, trades 2, trades/day 0.07, fees on
- W3 2026-05-01~2026-05-30: return -0.79%, PF 0.84, trades 5, trades/day 0.17, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (worst -3.50% < −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- ledger.next_priority: Encode daytrade-edge-15m-div-hold-v1: v1 hidden bull @ BB lower → BB upper only with take_profit null. No deploy. Keep v1–v3 frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 2767, warmup bars: 25)
Benchmark   +1.85%
Total Return -3.50%
CAGR        -36.17%
MDD         -3.99%
Sharpe      -5.19  (Rf=0, portfolio / full equity curve)
Sharpe      -11.75  (Rf=0, trades / position holding periods only)
Trades      10  Win Rate 30% (before fees)
Profit Factor  0.48 (before fees)
SL 0 / TP 3 / sell 7 / final_bar 0
Total Fees  9,840
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -17.47%
Total Return -1.12%
CAGR        -13.22%
MDD         -1.88%
Sharpe      -2.89  (Rf=0, portfolio / full equity curve)
Sharpe      -7.94  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 50% (before fees)
Profit Factor  0.46 (before fees)
SL 0 / TP 1 / sell 1 / final_bar 0
Total Fees  2,001
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -4.49%
Total Return -0.79%
CAGR        -9.53%
MDD         -1.84%
Sharpe      -1.64  (Rf=0, portfolio / full equity curve)
Sharpe      -3.11  (Rf=0, trades / position holding periods only)
Trades      5  Win Rate 40% (before fees)
Profit Factor  0.84 (before fees)
SL 0 / TP 2 / sell 3 / final_bar 0
Total Fees  4,997
```
