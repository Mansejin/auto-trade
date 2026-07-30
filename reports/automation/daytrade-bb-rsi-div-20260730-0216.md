# v59 FAIL

- slug: `daytrade-bb-rsi-div-v59`
- hypothesis: BTC daytrade long-only: BB 1.0σ wick low<lower + RSI rising RSI<35; exit RSI>=50.
- hypers: bb_std=1.0, pattern=wick_lower_rsi_up35, exit=rsi50_gte
- W1 2026-06-30~2026-07-29: return -3.88%, PF 1.36, trades 67, trades/day ≈2.23, fees on
- W2 2026-05-31~2026-06-29: return -12.87%, PF 0.78, trades 86, trades/day ≈2.87, fees on
- W3 2026-05-01~2026-05-30: return -9.08%, PF 0.89, trades 81, trades/day ≈2.70, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; tpd≈2.23/2.87/2.70 < 5.0)
- bar C: FAIL (worst -12.87% < −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: BB 1.0σ wick low<lower + RSI<45 flat (no rise); exit RSI>=48 — v60 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v60.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +1.79%
Total Return -3.88%
CAGR        -39.23%
MDD         -5.74%
Sharpe      -4.17  (Rf=0, portfolio / full equity curve)
Sharpe      9.56  (Rf=0, trades / position holding periods only)
Trades      67  Win Rate 73% (before fees)
Profit Factor  1.36 (before fees)
SL 8 / TP 0 / sell 59 / final_bar 0
Total Fees  66,195
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -17.77%
Total Return -12.87%
CAGR        -82.33%
MDD         -13.64%
Sharpe      -8.18  (Rf=0, portfolio / full equity curve)
Sharpe      -8.43  (Rf=0, trades / position holding periods only)
Trades      86  Win Rate 57% (before fees)
Profit Factor  0.78 (before fees)
SL 28 / TP 0 / sell 58 / final_bar 0
Total Fees  80,025
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.56%
Total Return -9.08%
CAGR        -69.83%
MDD         -10.50%
Sharpe      -9.43  (Rf=0, portfolio / full equity curve)
Sharpe      -3.54  (Rf=0, trades / position holding periods only)
Trades      81  Win Rate 64% (before fees)
Profit Factor  0.89 (before fees)
SL 12 / TP 0 / sell 69 / final_bar 0
Total Fees  77,803
```
