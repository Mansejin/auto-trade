# v51 FAIL

- slug: `daytrade-bb-rsi-div-v51`
- hypothesis: BTC daytrade long-only: 2-bar BB-lower soak (close≤lower ∧ close[1]≤lower[1]) + soft bull (low LL5 + RSI HL5) + RSI<42; exit BB middle only.
- hypers: pattern=two_bar_lower_soak_ll_hl5, exit=bb_mid_only, rsi_cap=42
- W1 2026-06-30~2026-07-29: return +0.20%, PF ∞, trades 1, trades/day ≈0.03, fees on
- W2 2026-05-31~2026-06-29: return -0.77%, PF 0.28, trades 2, trades/day ≈0.07, fees on
- W3 2026-05-01~2026-05-30: return -1.88%, PF 0.07, trades 4, trades/day ≈0.13, fees on
- bar A: FAIL (1/3 net>0; need ≥2/3)
- bar B: FAIL (passing W1 tpd≈0.03 < 5.0)
- bar C: PASS (worst -1.88%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: pierce close[1]<lower[1] then reclaim cross_above lower + LL/HL4 RSI<40 exit mid/RSI55 — v52 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v52.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 27)
Benchmark   +1.79%
Total Return +0.20%
CAGR        +2.60%
MDD         -0.05%
Sharpe      4.26  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,001
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -17.77%
Total Return -0.77%
CAGR        -9.32%
MDD         -1.05%
Sharpe      -2.57  (Rf=0, portfolio / full equity curve)
Sharpe      -27.33  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 50% (before fees)
Profit Factor  0.28 (before fees)
SL 1 / TP 0 / sell 1 / final_bar 0
Total Fees  1,997
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -4.56%
Total Return -1.88%
CAGR        -21.24%
MDD         -1.94%
Sharpe      -7.87  (Rf=0, portfolio / full equity curve)
Sharpe      -56.81  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 50% (before fees)
Profit Factor  0.07 (before fees)
SL 2 / TP 0 / sell 2 / final_bar 0
Total Fees  3,972
```
