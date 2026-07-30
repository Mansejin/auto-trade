# v68 FAIL

- slug: `daytrade-bb-rsi-div-v68`
- hypothesis: BTC daytrade long-only: prior close<BB lower then close cross_above lower + RSI cross_above rsi_signal RSI<45; exit mid.
- hypers: rsi_os=45, confirm=rsi_signal_cross, exit=bb_mid
- W1 2026-06-30~2026-07-29: return -3.51%, PF 1.15, trades 42, trades/day 1.4, fees on
- W2 2026-05-31~2026-06-29: return -7.48%, PF 0.67, trades 45, trades/day 1.5, fees on
- W3 2026-05-01~2026-05-30: return -4.75%, PF 0.97, trades 47, trades/day 1.57, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (worst -7.48% < −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- next_action: BB 2.5σ prior close<lower then close cross_above mid + LL/HL5 RSI<40; exit mid — v69 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v69.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +1.79%
Total Return -3.51%
CAGR        -36.25%
MDD         -4.26%
Sharpe      -5.99  (Rf=0, portfolio / full equity curve)
Sharpe      5.30  (Rf=0, trades / position holding periods only)
Trades      42  Win Rate 76% (before fees)
Profit Factor  1.15 (before fees)
SL 3 / TP 0 / sell 39 / final_bar 0
Total Fees  41,601
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -17.77%
Total Return -7.48%
CAGR        -62.42%
MDD         -8.21%
Sharpe      -8.80  (Rf=0, portfolio / full equity curve)
Sharpe      -15.30  (Rf=0, trades / position holding periods only)
Trades      45  Win Rate 62% (before fees)
Profit Factor  0.67 (before fees)
SL 11 / TP 0 / sell 34 / final_bar 0
Total Fees  42,599
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.56%
Total Return -4.75%
CAGR        -45.79%
MDD         -5.33%
Sharpe      -7.94  (Rf=0, portfolio / full equity curve)
Sharpe      -0.98  (Rf=0, trades / position holding periods only)
Trades      47  Win Rate 64% (before fees)
Profit Factor  0.97 (before fees)
SL 4 / TP 0 / sell 43 / final_bar 0
Total Fees  45,992
```
