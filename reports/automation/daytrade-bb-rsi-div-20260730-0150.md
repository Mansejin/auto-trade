# v54 FAIL

- slug: `daytrade-bb-rsi-div-v54`
- hypothesis: BTC daytrade long-only: after BB-lower pierce close[2]<lower[2], reclaim mid (close cross_above mid) + classic bull LL/HL3 + RSI<50; exit BB upper only.
- hypers: pattern=outer_then_mid_reclaim_ll_hl3, exit=bb_upper_only, rsi_cap=50
- W1 2026-06-30~2026-07-29: return +0.23%, PF ∞, trades 1, trades/day ≈0.03, fees on
- W2 2026-05-31~2026-06-29: return +0.74%, PF ∞, trades 2, trades/day ≈0.07, fees on
- W3 2026-05-01~2026-05-30: return +0.02%, PF ∞, trades 1, trades/day ≈0.03, fees on
- bar A: PASS (3/3 net>0 + zero-loss)
- bar B: FAIL (passing windows tpd≈0.03/0.07/0.03 < 5.0)
- bar C: PASS (worst +0.02%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: lower reclaim cross_above lower + LL/HL2 RSI<55 exit upper only — v55 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v55.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 25)
Benchmark   +1.79%
Total Return +0.23%
CAGR        +3.00%
MDD         -0.07%
Sharpe      2.81  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,001
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -17.77%
Total Return +0.74%
CAGR        +9.69%
MDD         -0.40%
Sharpe      3.48  (Rf=0, portfolio / full equity curve)
Sharpe      156.99  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 2 / final_bar 0
Total Fees  2,009
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -4.56%
Total Return +0.02%
CAGR        +0.22%
MDD         -0.05%
Sharpe      0.68  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,000
```
