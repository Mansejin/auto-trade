# v58 FAIL

- slug: `daytrade-bb-rsi-div-v58`
- hypothesis: BTC daytrade long-only: close still below BB 2.0σ lower + RSI rising RSI<40; exit close cross_above BB mid.
- hypers: bb_std=2.0, pattern=outside_lower_rsi_up40, exit=mid_cross
- W1 2026-06-30~2026-07-29: return -2.94%, PF 0.98, trades 29, trades/day ≈0.97, fees on
- W2 2026-05-31~2026-06-29: return -4.99%, PF 0.85, trades 39, trades/day ≈1.30, fees on
- W3 2026-05-01~2026-05-30: return -4.29%, PF 0.78, trades 32, trades/day ≈1.07, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; tpd≈0.97/1.30/1.07 < 5.0)
- bar C: FAIL (worst -4.99% < −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: BB 1.0σ wick low<lower + RSI rising RSI<35; exit RSI>=50 — v59 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v59.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +1.79%
Total Return -2.94%
CAGR        -31.28%
MDD         -4.08%
Sharpe      -4.80  (Rf=0, portfolio / full equity curve)
Sharpe      -0.43  (Rf=0, trades / position holding periods only)
Trades      29  Win Rate 62% (before fees)
Profit Factor  0.98 (before fees)
SL 5 / TP 0 / sell 24 / final_bar 0
Total Fees  28,468
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -17.77%
Total Return -4.99%
CAGR        -47.48%
MDD         -5.44%
Sharpe      -5.49  (Rf=0, portfolio / full equity curve)
Sharpe      -5.37  (Rf=0, trades / position holding periods only)
Trades      39  Win Rate 62% (before fees)
Profit Factor  0.85 (before fees)
SL 8 / TP 0 / sell 31 / final_bar 0
Total Fees  37,734
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.56%
Total Return -4.29%
CAGR        -42.38%
MDD         -5.32%
Sharpe      -7.70  (Rf=0, portfolio / full equity curve)
Sharpe      -7.83  (Rf=0, trades / position holding periods only)
Trades      32  Win Rate 53% (before fees)
Profit Factor  0.78 (before fees)
SL 5 / TP 0 / sell 27 / final_bar 0
Total Fees  31,440
```
