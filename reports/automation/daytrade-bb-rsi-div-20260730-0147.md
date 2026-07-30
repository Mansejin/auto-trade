# v53 FAIL

- slug: `daytrade-bb-rsi-div-v53`
- hypothesis: BTC daytrade long-only: delayed reclaim after pierce (close[2]<BB lower[2], close[1]<BB mid[1]) then close cross_above lower + soft bull LL/HL6 + RSI<45; exit BB mid only.
- hypers: pattern=delayed_pierce_reclaim_ll_hl6, exit=bb_mid_only, rsi_cap=45
- W1 2026-06-30~2026-07-29: return -0.32%, PF 1.52, trades 8, trades/day ≈0.27, fees on
- W2 2026-05-31~2026-06-29: return -1.83%, PF 0.47, trades 8, trades/day ≈0.27, fees on
- W3 2026-05-01~2026-05-30: return -4.52%, PF 0.11, trades 12, trades/day ≈0.40, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; max tpd≈0.40)
- bar C: FAIL (worst -4.52%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: outer pierce close[2]<lower[2] then mid reclaim cross_above mid + LL/HL3 RSI<50 exit upper only — v54 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v54.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 28)
Benchmark   +1.79%
Total Return -0.32%
CAGR        -3.92%
MDD         -1.07%
Sharpe      -1.12  (Rf=0, portfolio / full equity curve)
Sharpe      18.06  (Rf=0, trades / position holding periods only)
Trades      8  Win Rate 75% (before fees)
Profit Factor  1.52 (before fees)
SL 1 / TP 0 / sell 7 / final_bar 0
Total Fees  8,023
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 28)
Benchmark   -17.77%
Total Return -1.83%
CAGR        -20.75%
MDD         -2.54%
Sharpe      -4.14  (Rf=0, portfolio / full equity curve)
Sharpe      -25.47  (Rf=0, trades / position holding periods only)
Trades      8  Win Rate 62% (before fees)
Profit Factor  0.47 (before fees)
SL 2 / TP 0 / sell 6 / final_bar 0
Total Fees  7,946
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 28)
Benchmark   -4.56%
Total Return -4.52%
CAGR        -44.12%
MDD         -4.53%
Sharpe      -11.29  (Rf=0, portfolio / full equity curve)
Sharpe      -57.64  (Rf=0, trades / position holding periods only)
Trades      12  Win Rate 33% (before fees)
Profit Factor  0.11 (before fees)
SL 4 / TP 0 / sell 8 / final_bar 0
Total Fees  11,765
```
