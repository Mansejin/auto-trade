# v56 FAIL

- slug: `daytrade-bb-rsi-div-v56`
- hypothesis: BTC daytrade long-only: tighter BB 1.5σ lower reclaim + micro bull LL/HL1 + RSI<50; exit BB mid only.
- hypers: bb_std=1.5, pattern=lower_reclaim_ll_hl1, exit=bb_mid_only
- W1 2026-06-30~2026-07-29: return -8.19%, PF 1.23, trades 103, trades/day ≈3.43, fees on
- W2 2026-05-31~2026-06-29: return -17.75%, PF 0.61, trades 110, trades/day ≈3.67, fees on
- W3 2026-05-01~2026-05-30: return -8.26%, PF 1.24, trades 107, trades/day ≈3.57, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; tpd≈3.43/3.67/3.57)
- bar C: FAIL (worst -17.75% < −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: BB 1.5σ pierce1 then mid reclaim LL/HL2 RSI<55 exit upper — v57 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v57.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +1.79%
Total Return -8.19%
CAGR        -65.90%
MDD         -9.11%
Sharpe      -9.60  (Rf=0, portfolio / full equity curve)
Sharpe      7.01  (Rf=0, trades / position holding periods only)
Trades      103  Win Rate 72% (before fees)
Profit Factor  1.23 (before fees)
SL 5 / TP 0 / sell 98 / final_bar 0
Total Fees  98,830
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -17.77%
Total Return -17.75%
CAGR        -91.46%
MDD         -17.75%
Sharpe      -15.49  (Rf=0, portfolio / full equity curve)
Sharpe      -19.28  (Rf=0, trades / position holding periods only)
Trades      110  Win Rate 62% (before fees)
Profit Factor  0.61 (before fees)
SL 25 / TP 0 / sell 85 / final_bar 0
Total Fees  97,744
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.56%
Total Return -8.26%
CAGR        -66.20%
MDD         -9.12%
Sharpe      -11.43  (Rf=0, portfolio / full equity curve)
Sharpe      7.87  (Rf=0, trades / position holding periods only)
Trades      107  Win Rate 71% (before fees)
Profit Factor  1.24 (before fees)
SL 6 / TP 0 / sell 101 / final_bar 0
Total Fees  102,041
```
