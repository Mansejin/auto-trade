# v64 FAIL

- slug: `daytrade-bb-rsi-div-v64`
- hypothesis: BTC daytrade long-only: BB 1.2σ close<lower + price LL2 RSI HL2 RSI<35; exit RSI>=70.
- hypers: bb_std=1.2, div_lookback=2, exit=rsi70_gte
- W1 2026-06-30~2026-07-29: return +0.14%, PF 1.37, trades 43, trades/day ≈1.43, fees on
- W2 2026-05-31~2026-06-29: return -4.06%, PF 1.04, trades 52, trades/day ≈1.73, fees on
- W3 2026-05-01~2026-05-30: return -2.12%, PF 1.19, trades 46, trades/day ≈1.53, fees on
- bar A: FAIL (1/3 net>0&PF≥1.2; only W1)
- bar B: FAIL (W1 tpd≈1.43 <5; no other pass window)
- bar C: FAIL (worst -4.06% < −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: BB 1.0σ close≤lower + price LL3 + RSI cross_above rsi_signal RSI<40; exit mid cross — v65 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v65.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 24)
Benchmark   +1.79%
Total Return +0.14%
CAGR        +1.82%
MDD         -4.72%
Sharpe      0.19  (Rf=0, portfolio / full equity curve)
Sharpe      5.06  (Rf=0, trades / position holding periods only)
Trades      43  Win Rate 63% (before fees)
Profit Factor  1.37 (before fees)
SL 15 / TP 0 / sell 27 / final_bar 1
Total Fees  43,580
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -17.77%
Total Return -4.06%
CAGR        -40.66%
MDD         -10.78%
Sharpe      -1.63  (Rf=0, portfolio / full equity curve)
Sharpe      1.00  (Rf=0, trades / position holding periods only)
Trades      52  Win Rate 42% (before fees)
Profit Factor  1.04 (before fees)
SL 30 / TP 3 / sell 19 / final_bar 0
Total Fees  49,327
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -4.56%
Total Return -2.12%
CAGR        -23.60%
MDD         -8.39%
Sharpe      -1.60  (Rf=0, portfolio / full equity curve)
Sharpe      3.28  (Rf=0, trades / position holding periods only)
Trades      46  Win Rate 57% (before fees)
Profit Factor  1.19 (before fees)
SL 16 / TP 0 / sell 30 / final_bar 0
Total Fees  46,886
```
