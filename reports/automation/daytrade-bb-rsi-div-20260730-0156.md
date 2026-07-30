# v55 FAIL

- slug: `daytrade-bb-rsi-div-v55`
- hypothesis: BTC daytrade long-only: close cross_above BB lower + classic bull LL/HL2 + RSI<55; exit BB upper only.
- hypers: pattern=lower_reclaim_ll_hl2, exit=bb_upper_only, rsi_cap=55
- W1 2026-06-30~2026-07-29: return -1.67%, PF 1.50, trades 76, trades/day ≈2.53, fees on
- W2 2026-05-31~2026-06-29: return -10.02%, PF 0.97, trades 100, trades/day ≈3.33, fees on
- W3 2026-05-01~2026-05-30: return -5.10%, PF 1.22, trades 82, trades/day ≈2.73, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (tpd≈2.53/3.33/2.73 < 5.0)
- bar C: FAIL (worst -10.02% < −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: BB 1.5σ lower reclaim LL/HL1 RSI<50 exit mid — v56 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v56.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 24)
Benchmark   +1.79%
Total Return -1.67%
CAGR        -19.05%
MDD         -5.05%
Sharpe      -1.22  (Rf=0, portfolio / full equity curve)
Sharpe      9.64  (Rf=0, trades / position holding periods only)
Trades      76  Win Rate 74% (before fees)
Profit Factor  1.50 (before fees)
SL 13 / TP 0 / sell 62 / final_bar 1
Total Fees  74,919
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -17.77%
Total Return -10.02%
CAGR        -73.51%
MDD         -11.96%
Sharpe      -4.58  (Rf=0, portfolio / full equity curve)
Sharpe      -0.18  (Rf=0, trades / position holding periods only)
Trades      100  Win Rate 50% (before fees)
Profit Factor  0.97 (before fees)
SL 39 / TP 2 / sell 58 / final_bar 1
Total Fees  92,253
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -4.56%
Total Return -5.10%
CAGR        -48.23%
MDD         -9.20%
Sharpe      -4.02  (Rf=0, portfolio / full equity curve)
Sharpe      4.54  (Rf=0, trades / position holding periods only)
Trades      82  Win Rate 71% (before fees)
Profit Factor  1.22 (before fees)
SL 16 / TP 0 / sell 66 / final_bar 0
Total Fees  82,051
```
