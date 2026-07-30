# v66 FAIL

- slug: `daytrade-bb-rsi-div-v66`
- hypothesis: BTC daytrade long-only: prior close<BB lower then close cross_above lower + LL/HL4 RSI<45; exit upper.
- hypers: bb_std=2.0, div_lookback=4, exit=bb_upper
- W1 2026-06-30~2026-07-29: return -3.68%, PF 0.99, trades 37, trades/day ≈1.23, fees on
- W2 2026-05-31~2026-06-29: return -1.32%, PF 1.26, trades 51, trades/day ≈1.70, fees on
- W3 2026-05-01~2026-05-30: return -2.92%, PF 1.18, trades 43, trades/day ≈1.43, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (worst -3.68% < −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- next_action: wick low<BB lower + close cross_above mid + LL/HL5 RSI<40; exit RSI>=55 — v67 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v67.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 26)
Benchmark   +1.79%
Total Return -3.68%
CAGR        -37.60%
MDD         -5.06%
Sharpe      -3.92  (Rf=0, portfolio / full equity curve)
Sharpe      0.01  (Rf=0, trades / position holding periods only)
Trades      37  Win Rate 62% (before fees)
Profit Factor  0.99 (before fees)
SL 8 / TP 0 / sell 29 / final_bar 0
Total Fees  35,932
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -17.77%
Total Return -1.32%
CAGR        -15.35%
MDD         -9.62%
Sharpe      -0.70  (Rf=0, portfolio / full equity curve)
Sharpe      5.74  (Rf=0, trades / position holding periods only)
Trades      51  Win Rate 53% (before fees)
Profit Factor  1.26 (before fees)
SL 17 / TP 2 / sell 31 / final_bar 1
Total Fees  48,939
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -4.56%
Total Return -2.92%
CAGR        -31.10%
MDD         -6.15%
Sharpe      -3.14  (Rf=0, portfolio / full equity curve)
Sharpe      3.74  (Rf=0, trades / position holding periods only)
Trades      43  Win Rate 70% (before fees)
Profit Factor  1.18 (before fees)
SL 9 / TP 0 / sell 34 / final_bar 0
Total Fees  43,573
```
