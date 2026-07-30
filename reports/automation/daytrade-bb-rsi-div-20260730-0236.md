# v63 FAIL

- slug: `daytrade-bb-rsi-div-v63`
- hypothesis: BTC daytrade long-only: BB 1.0σ close<lower + price LL3 RSI HL3 RSI<40; exit RSI>=65.
- hypers: bb_std=1.0, div_lookback=3, exit=rsi65_gte
- W1 2026-06-30~2026-07-29: return -6.91%, PF 1.00, trades 72, trades/day ≈2.40, fees on
- W2 2026-05-31~2026-06-29: return -0.99%, PF 1.25, trades 96, trades/day ≈3.20, fees on
- W3 2026-05-01~2026-05-30: return -5.81%, PF 1.11, trades 77, trades/day ≈2.57, fees on
- bar A: FAIL (0/3 net>0&PF≥1.2)
- bar B: FAIL (no passing window; tpd≈2.40/3.20/2.57 all <5)
- bar C: FAIL (worst -6.91% < −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: BB 1.2σ close<lower + price LL2 RSI HL2 RSI<35; exit RSI>=70 — v64 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v64.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 25)
Benchmark   +1.79%
Total Return -6.91%
CAGR        -59.40%
MDD         -8.37%
Sharpe      -4.52  (Rf=0, portfolio / full equity curve)
Sharpe      0.18  (Rf=0, trades / position holding periods only)
Trades      72  Win Rate 64% (before fees)
Profit Factor  1.00 (before fees)
SL 23 / TP 0 / sell 48 / final_bar 1
Total Fees  69,069
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -17.77%
Total Return -0.99%
CAGR        -11.76%
MDD         -13.77%
Sharpe      -0.26  (Rf=0, portfolio / full equity curve)
Sharpe      5.71  (Rf=0, trades / position holding periods only)
Trades      96  Win Rate 54% (before fees)
Profit Factor  1.25 (before fees)
SL 43 / TP 2 / sell 50 / final_bar 1
Total Fees  90,337
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -4.56%
Total Return -5.81%
CAGR        -52.95%
MDD         -9.21%
Sharpe      -4.06  (Rf=0, portfolio / full equity curve)
Sharpe      2.07  (Rf=0, trades / position holding periods only)
Trades      77  Win Rate 66% (before fees)
Profit Factor  1.11 (before fees)
SL 20 / TP 0 / sell 56 / final_bar 1
Total Fees  75,840
```
