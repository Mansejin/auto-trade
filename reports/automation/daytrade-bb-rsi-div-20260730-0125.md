# v49 FAIL

- slug: `daytrade-bb-rsi-div-v49`
- hypothesis: BTC daytrade long-only: OR (A) close cross_above BB lower + RSI HL1 + RSI<45 OR (B) low LL2 + RSI HL2 at/below BB lower; exit BB mid or RSI≥60.
- hypers: pattern=or_reclaim_hl1_or_soft_ll_hl2, exit=bb_mid_or_rsi60, rsi_cap=45
- W1 2026-06-30~2026-07-29: return -13.71%, PF 1.20, trades 178, trades/day ≈5.93, fees on
- W2 2026-05-31~2026-06-29: return -23.55%, PF 0.81, trades 197, trades/day ≈6.57, fees on
- W3 2026-05-01~2026-05-30: return -16.53%, PF 0.92, trades 164, trades/day ≈5.47, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; tpd≈5.93/6.57/5.47)
- bar C: FAIL (worst -23.55%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: classic LL6+RSI HL6 close<BB lower RSI<35 exit BB upper only — v50 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v50.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 24)
Benchmark   +1.79%
Total Return -13.71%
CAGR        -84.36%
MDD         -15.02%
Sharpe      -12.14  (Rf=0, portfolio / full equity curve)
Sharpe      5.96  (Rf=0, trades / position holding periods only)
Trades      178  Win Rate 73% (before fees)
Profit Factor  1.20 (before fees)
SL 15 / TP 0 / sell 163 / final_bar 0
Total Fees  168,570
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -17.77%
Total Return -23.55%
CAGR        -96.59%
MDD         -24.42%
Sharpe      -12.43  (Rf=0, portfolio / full equity curve)
Sharpe      -7.00  (Rf=0, trades / position holding periods only)
Trades      197  Win Rate 61% (before fees)
Profit Factor  0.81 (before fees)
SL 44 / TP 1 / sell 152 / final_bar 0
Total Fees  167,605
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -4.56%
Total Return -16.53%
CAGR        -89.71%
MDD         -17.31%
Sharpe      -15.58  (Rf=0, portfolio / full equity curve)
Sharpe      -3.06  (Rf=0, trades / position holding periods only)
Trades      164  Win Rate 62% (before fees)
Profit Factor  0.92 (before fees)
SL 14 / TP 0 / sell 150 / final_bar 0
Total Fees  151,601
```
