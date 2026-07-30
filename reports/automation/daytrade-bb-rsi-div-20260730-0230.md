# v62 FAIL

- slug: `daytrade-bb-rsi-div-v62`
- hypothesis: BTC daytrade long-only: BB 1.5σ close<lower + price LL4 RSI HL4 RSI<40; exit RSI>=60.
- hypers: bb_std=1.5, div_lookback=4, exit=rsi60_gte
- W1 2026-06-30~2026-07-29: return +4.87%, PF 2.81, trades 43, trades/day ≈1.43, fees on
- W2 2026-05-31~2026-06-29: return -3.50%, PF 1.09, trades 54, trades/day ≈1.80, fees on
- W3 2026-05-01~2026-05-30: return -2.51%, PF 1.25, trades 45, trades/day ≈1.50, fees on
- bar A: FAIL (1/3 net>0&PF≥1.2; only W1)
- bar B: FAIL (W1 tpd≈1.43 < 5)
- bar C: FAIL (worst -3.50% < −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: BB 1.0σ close<lower + price LL3 RSI HL3 RSI<40; exit RSI>=65 — v63 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v63.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 26)
Benchmark   +1.79%
Total Return +4.87%
CAGR        +81.83%
MDD         -1.93%
Sharpe      4.55  (Rf=0, portfolio / full equity curve)
Sharpe      25.49  (Rf=0, trades / position holding periods only)
Trades      43  Win Rate 81% (before fees)
Profit Factor  2.81 (before fees)
SL 6 / TP 0 / sell 36 / final_bar 1
Total Fees  43,734
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -17.77%
Total Return -3.50%
CAGR        -36.10%
MDD         -9.80%
Sharpe      -1.86  (Rf=0, portfolio / full equity curve)
Sharpe      2.80  (Rf=0, trades / position holding periods only)
Trades      54  Win Rate 54% (before fees)
Profit Factor  1.09 (before fees)
SL 23 / TP 1 / sell 30 / final_bar 0
Total Fees  51,348
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -4.56%
Total Return -2.51%
CAGR        -27.34%
MDD         -6.30%
Sharpe      -2.60  (Rf=0, portfolio / full equity curve)
Sharpe      5.18  (Rf=0, trades / position holding periods only)
Trades      45  Win Rate 71% (before fees)
Profit Factor  1.25 (before fees)
SL 10 / TP 0 / sell 35 / final_bar 0
Total Fees  45,385
```
