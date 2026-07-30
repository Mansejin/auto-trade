# v50 FAIL

- slug: `daytrade-bb-rsi-div-v50`
- hypothesis: BTC daytrade long-only: classic bull (low LL6 + RSI HL6) when close < BB lower and RSI < 35; exit BB upper only.
- hypers: pattern=classic_ll_hl6_close_below_lower, exit=bb_upper_only, rsi_cap=35
- W1 2026-06-30~2026-07-29: return -0.73%, PF 0.62, trades 4, trades/day ≈0.13, fees on
- W2 2026-05-31~2026-06-29: return -1.36%, PF 0.33, trades 3, trades/day ≈0.1, fees on
- W3 2026-05-01~2026-05-30: return -0.41%, PF 0.74, trades 2, trades/day ≈0.07, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (tpd≈0.13/0.1/0.07)
- bar C: PASS (worst -1.36%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: 2-bar close≤BB lower soak + soft LL/HL5 RSI<42 exit mid only — v51 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v51.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 28)
Benchmark   +1.79%
Total Return -0.73%
CAGR        -8.84%
MDD         -1.20%
Sharpe      -2.57  (Rf=0, portfolio / full equity curve)
Sharpe      -9.04  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 50% (before fees)
Profit Factor  0.62 (before fees)
SL 1 / TP 0 / sell 3 / final_bar 0
Total Fees  3,973
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 28)
Benchmark   -17.77%
Total Return -1.36%
CAGR        -15.83%
MDD         -2.39%
Sharpe      -4.10  (Rf=0, portfolio / full equity curve)
Sharpe      -31.65  (Rf=0, trades / position holding periods only)
Trades      3  Win Rate 33% (before fees)
Profit Factor  0.33 (before fees)
SL 2 / TP 0 / sell 1 / final_bar 0
Total Fees  2,966
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 28)
Benchmark   -4.56%
Total Return -0.41%
CAGR        -5.03%
MDD         -1.61%
Sharpe      -1.31  (Rf=0, portfolio / full equity curve)
Sharpe      -8.44  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 50% (before fees)
Profit Factor  0.74 (before fees)
SL 1 / TP 0 / sell 1 / final_bar 0
Total Fees  1,989
```
