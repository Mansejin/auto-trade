# v65 FAIL

- slug: `daytrade-bb-rsi-div-v65`
- hypothesis: BTC daytrade long-only: BB 1.0σ close≤lower + price LL3 + RSI cross_above rsi_signal RSI<40; exit mid cross.
- hypers: bb_std=1.0, div_lookback=3, exit=mid_cross
- W1 2026-06-30~2026-07-29: return -4.86%, PF 0.96, trades 47, trades/day ≈1.57, fees on
- W2 2026-05-31~2026-06-29: return -6.91%, PF 0.87, trades 55, trades/day ≈1.83, fees on
- W3 2026-05-01~2026-05-30: return -5.19%, PF 1.04, trades 56, trades/day ≈1.87, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (worst -6.91% < −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- next_action: prior close<BB lower then close cross_above lower + LL/HL4 RSI<45; exit upper — v66 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v66.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +1.79%
Total Return -4.86%
CAGR        -46.59%
MDD         -5.42%
Sharpe      -7.58  (Rf=0, portfolio / full equity curve)
Sharpe      -1.79  (Rf=0, trades / position holding periods only)
Trades      47  Win Rate 70% (before fees)
Profit Factor  0.96 (before fees)
SL 5 / TP 0 / sell 42 / final_bar 0
Total Fees  46,387
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -17.77%
Total Return -6.91%
CAGR        -59.39%
MDD         -7.49%
Sharpe      -6.64  (Rf=0, portfolio / full equity curve)
Sharpe      -5.72  (Rf=0, trades / position holding periods only)
Trades      55  Win Rate 62% (before fees)
Profit Factor  0.87 (before fees)
SL 14 / TP 0 / sell 41 / final_bar 0
Total Fees  52,874
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.56%
Total Return -5.19%
CAGR        -48.86%
MDD         -5.95%
Sharpe      -7.87  (Rf=0, portfolio / full equity curve)
Sharpe      1.68  (Rf=0, trades / position holding periods only)
Trades      56  Win Rate 70% (before fees)
Profit Factor  1.04 (before fees)
SL 6 / TP 0 / sell 50 / final_bar 0
Total Fees  54,364
```
