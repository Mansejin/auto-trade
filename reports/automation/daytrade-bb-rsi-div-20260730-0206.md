# v57 FAIL

- slug: `daytrade-bb-rsi-div-v57`
- hypothesis: BTC daytrade long-only: BB 1.5σ pierce close[1]<lower[1] then mid reclaim + soft bull LL/HL2 RSI<55; exit BB upper only.
- hypers: bb_std=1.5, pattern=pierce1_mid_reclaim_ll_hl2, exit=bb_upper_only
- W1 2026-06-30~2026-07-29: return +0.03%, PF ∞, trades 3, trades/day ≈0.10, fees on
- W2 2026-05-31~2026-06-29: return -0.90%, PF 0.74, trades 5, trades/day ≈0.17, fees on
- W3 2026-05-01~2026-05-30: return -0.82%, PF 0.98, trades 8, trades/day ≈0.27, fees on
- bar A: FAIL (1/3 net>0; only W1)
- bar B: FAIL (passing W1 tpd≈0.10 < 5.0)
- bar C: PASS (worst -0.90% ≥ −2%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: close still < BB 2.0σ lower + RSI rising RSI<40; exit mid cross — v58 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v58.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 24)
Benchmark   +1.79%
Total Return +0.03%
CAGR        +0.42%
MDD         -0.38%
Sharpe      0.29  (Rf=0, portfolio / full equity curve)
Sharpe      199.36  (Rf=0, trades / position holding periods only)
Trades      3  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 3 / final_bar 0
Total Fees  3,002
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -17.77%
Total Return -0.90%
CAGR        -10.80%
MDD         -2.26%
Sharpe      -2.82  (Rf=0, portfolio / full equity curve)
Sharpe      -8.10  (Rf=0, trades / position holding periods only)
Trades      5  Win Rate 60% (before fees)
Profit Factor  0.74 (before fees)
SL 2 / TP 0 / sell 3 / final_bar 0
Total Fees  4,941
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -4.56%
Total Return -0.82%
CAGR        -9.81%
MDD         -1.03%
Sharpe      -4.17  (Rf=0, portfolio / full equity curve)
Sharpe      -0.72  (Rf=0, trades / position holding periods only)
Trades      8  Win Rate 88% (before fees)
Profit Factor  0.98 (before fees)
SL 1 / TP 0 / sell 7 / final_bar 0
Total Fees  8,001
```
