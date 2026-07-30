# v60 FAIL

- slug: `daytrade-bb-rsi-div-v60`
- hypothesis: BTC daytrade long-only: BB 1.0σ wick low<lower + RSI<45 flat (no rise); exit RSI>=48.
- hypers: bb_std=1.0, pattern=wick_lower_rsi45_flat, exit=rsi48_gte
- W1 2026-06-30~2026-07-29: return -25.19%, PF 1.11, trades 313, trades/day ≈10.43, fees on
- W2 2026-05-31~2026-06-29: return -32.64%, PF 0.95, trades 379, trades/day ≈12.63, fees on
- W3 2026-05-01~2026-05-30: return -27.86%, PF 0.92, trades 302, trades/day ≈10.07, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; tpd≈10.43/12.63/10.07 ≥5 but A fail)
- bar C: FAIL (worst -32.64% < −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: BB 1.0σ wick low<lower + price LL3 RSI HL3 RSI<50; exit mid cross — v61 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v61.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +1.79%
Total Return -25.19%
CAGR        -97.41%
MDD         -25.58%
Sharpe      -18.57  (Rf=0, portfolio / full equity curve)
Sharpe      2.93  (Rf=0, trades / position holding periods only)
Trades      313  Win Rate 72% (before fees)
Profit Factor  1.11 (before fees)
SL 22 / TP 0 / sell 291 / final_bar 0
Total Fees  276,879
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -17.77%
Total Return -32.64%
CAGR        -99.31%
MDD         -33.58%
Sharpe      -15.16  (Rf=0, portfolio / full equity curve)
Sharpe      -0.78  (Rf=0, trades / position holding periods only)
Trades      379  Win Rate 68% (before fees)
Profit Factor  0.95 (before fees)
SL 71 / TP 0 / sell 308 / final_bar 0
Total Fees  302,466
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.56%
Total Return -27.86%
CAGR        -98.36%
MDD         -28.10%
Sharpe      -22.53  (Rf=0, portfolio / full equity curve)
Sharpe      -2.86  (Rf=0, trades / position holding periods only)
Trades      302  Win Rate 70% (before fees)
Profit Factor  0.92 (before fees)
SL 23 / TP 0 / sell 279 / final_bar 0
Total Fees  260,775
```
