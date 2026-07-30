# v46 FAIL

- slug: `daytrade-bb-rsi-div-v46`
- hypothesis: BTC daytrade long-only: RSI hysteresis leave (prior<35∧≥40) while close≤BB middle; exit BB upper only.
- hypers: pattern=rsi_hysteresis_35_40_below_mid, exit=bb_upper_only, rsi_os_lo=35
- W1 2026-06-29~2026-07-28: return -0.88%, PF 1.57, trades 44, trades/day ≈1.47, fees on
- W2 2026-05-30~2026-06-28: return -12.47%, PF 0.67, trades 60, trades/day ≈2.0, fees on
- W3 2026-04-30~2026-05-29: return -6.30%, PF 0.95, trades 58, trades/day ≈1.93, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; max tpd≈2.0)
- bar C: FAIL (worst -12.47%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: classic LL/HL10 green @BB lower → mid/RSI55 — v47 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v47.json` validate OK

### W1 stdout
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -0.88%
CAGR        -10.57%
MDD         -2.54%
Sharpe      -0.81  (Rf=0, portfolio / full equity curve)
Sharpe      11.26  (Rf=0, trades / position holding periods only)
Trades      44  Win Rate 75% (before fees)
Profit Factor  1.57 (before fees)
SL 7 / TP 0 / sell 37 / final_bar 0
Total Fees  43,673
```

### W2 stdout
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -12.47%
CAGR        -81.30%
MDD         -12.84%
Sharpe      -8.48  (Rf=0, portfolio / full equity curve)
Sharpe      -11.34  (Rf=0, trades / position holding periods only)
Trades      60  Win Rate 47% (before fees)
Profit Factor  0.67 (before fees)
SL 26 / TP 1 / sell 33 / final_bar 0
Total Fees  56,131
```

### W3 stdout
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return -6.30%
CAGR        -55.89%
MDD         -7.85%
Sharpe      -6.83  (Rf=0, portfolio / full equity curve)
Sharpe      -1.52  (Rf=0, trades / position holding periods only)
Trades      58  Win Rate 71% (before fees)
Profit Factor  0.95 (before fees)
SL 12 / TP 0 / sell 46 / final_bar 0
Total Fees  57,902
```
