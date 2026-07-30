# v61 FAIL

- slug: `daytrade-bb-rsi-div-v61`
- hypothesis: BTC daytrade long-only: BB 1.0σ wick low<lower + price LL3 RSI HL3 RSI<50; exit mid cross.
- hypers: bb_std=1.0, div_lookback=3, exit=mid_cross
- W1 2026-06-30~2026-07-29: return -16.90%, PF 1.09, trades 200, trades/day ≈6.67, fees on
- W2 2026-05-31~2026-06-29: return -28.37%, PF 0.79, trades 243, trades/day ≈8.10, fees on
- W3 2026-05-01~2026-05-30: return -16.88%, PF 1.05, trades 193, trades/day ≈6.43, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; tpd≈6.67/8.10/6.43 ≥5 but A fail)
- bar C: FAIL (worst -28.37% < −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: BB 1.5σ close<lower + price LL4 RSI HL4 RSI<40; exit RSI>=60 — v62 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v62.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 25)
Benchmark   +1.79%
Total Return -16.90%
CAGR        -90.27%
MDD         -17.59%
Sharpe      -15.19  (Rf=0, portfolio / full equity curve)
Sharpe      3.08  (Rf=0, trades / position holding periods only)
Trades      200  Win Rate 72% (before fees)
Profit Factor  1.09 (before fees)
SL 14 / TP 0 / sell 186 / final_bar 0
Total Fees  182,826
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -17.77%
Total Return -28.37%
CAGR        -98.50%
MDD         -29.04%
Sharpe      -15.60  (Rf=0, portfolio / full equity curve)
Sharpe      -7.53  (Rf=0, trades / position holding periods only)
Trades      243  Win Rate 63% (before fees)
Profit Factor  0.79 (before fees)
SL 57 / TP 2 / sell 184 / final_bar 0
Total Fees  198,539
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -4.56%
Total Return -16.88%
CAGR        -90.24%
MDD         -17.76%
Sharpe      -15.25  (Rf=0, portfolio / full equity curve)
Sharpe      1.58  (Rf=0, trades / position holding periods only)
Trades      193  Win Rate 68% (before fees)
Profit Factor  1.05 (before fees)
SL 13 / TP 0 / sell 179 / final_bar 1
Total Fees  177,663
```
