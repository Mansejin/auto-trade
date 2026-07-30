# v67 FAIL

- slug: `daytrade-bb-rsi-div-v67`
- hypothesis: BTC daytrade long-only: wick low<BB lower + close cross_above mid + LL/HL5 RSI<40; exit RSI>=55.
- hypers: rsi_os=40, div_lookback=5, exit=rsi55_gte
- W1 2026-06-30~2026-07-29: return +0.00%, PF N/A, trades 0, trades/day 0, fees on
- W2 2026-05-31~2026-06-29: return +0.00%, PF N/A, trades 0, trades/day 0, fees on
- W3 2026-05-01~2026-05-30: return +0.00%, PF N/A, trades 0, trades/day 0, fees on
- bar A: FAIL (0/3 net>0)
- bar B: PASS (worst +0.00% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: none
- next_action: prior close<BB lower then close cross_above lower + RSI cross_above rsi_signal RSI<45; exit mid — v68 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v68.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 27)
Benchmark   +1.79%
Total Return +0.00%
CAGR        +0.00%
MDD         0.00%
Sharpe      0.00  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      0  Win Rate N/A (0 executed trades) (before fees)
Profit Factor  N/A (0 executed trades) (before fees)
SL 0 / TP 0 / sell 0 / final_bar 0
Total Fees  0
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -17.77%
Total Return +0.00%
CAGR        +0.00%
MDD         0.00%
Sharpe      0.00  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      0  Win Rate N/A (0 executed trades) (before fees)
Profit Factor  N/A (0 executed trades) (before fees)
SL 0 / TP 0 / sell 0 / final_bar 0
Total Fees  0
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -4.56%
Total Return +0.00%
CAGR        +0.00%
MDD         0.00%
Sharpe      0.00  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      0  Win Rate N/A (0 executed trades) (before fees)
Profit Factor  N/A (0 executed trades) (before fees)
SL 0 / TP 0 / sell 0 / final_bar 0
Total Fees  0
```
