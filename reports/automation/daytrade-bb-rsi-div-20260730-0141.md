# v52 FAIL

- slug: `daytrade-bb-rsi-div-v52`
- hypothesis: BTC daytrade long-only: prior pierce close[1]<BB lower[1], reclaim close cross_above lower + soft bull (low LL4 + RSI HL4) + RSI<40; exit BB mid or RSI≥55.
- hypers: pattern=pierce_reclaim_ll_hl4, exit=bb_mid_or_rsi55, rsi_cap=40
- W1 2026-06-30~2026-07-29: return -2.26%, PF 0.93, trades 21, trades/day ≈0.70, fees on
- W2 2026-05-31~2026-06-29: return -1.94%, PF 1.28, trades 39, trades/day ≈1.30, fees on
- W3 2026-05-01~2026-05-30: return -4.83%, PF 0.71, trades 34, trades/day ≈1.13, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; max tpd≈1.30)
- bar C: FAIL (worst -4.83%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: delayed pierce reclaim close[2]<lower[2] close[1]<mid[1] cross_above lower + LL/HL6 RSI<45 exit mid only — v53 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v53.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 26)
Benchmark   +1.79%
Total Return -2.26%
CAGR        -24.96%
MDD         -2.92%
Sharpe      -4.89  (Rf=0, portfolio / full equity curve)
Sharpe      -2.40  (Rf=0, trades / position holding periods only)
Trades      21  Win Rate 67% (before fees)
Profit Factor  0.93 (before fees)
SL 2 / TP 0 / sell 19 / final_bar 0
Total Fees  20,831
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -17.77%
Total Return -1.94%
CAGR        -21.84%
MDD         -5.38%
Sharpe      -1.75  (Rf=0, portfolio / full equity curve)
Sharpe      9.19  (Rf=0, trades / position holding periods only)
Trades      39  Win Rate 69% (before fees)
Profit Factor  1.28 (before fees)
SL 7 / TP 0 / sell 32 / final_bar 0
Total Fees  38,112
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -4.56%
Total Return -4.83%
CAGR        -46.37%
MDD         -5.41%
Sharpe      -8.11  (Rf=0, portfolio / full equity curve)
Sharpe      -11.11  (Rf=0, trades / position holding periods only)
Trades      34  Win Rate 56% (before fees)
Profit Factor  0.71 (before fees)
SL 5 / TP 0 / sell 29 / final_bar 0
Total Fees  33,438
```
