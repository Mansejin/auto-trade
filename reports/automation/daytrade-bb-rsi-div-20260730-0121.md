# v48 FAIL

- slug: `daytrade-bb-rsi-div-v48`
- hypothesis: BTC daytrade long-only: micro bull (low LL1 + RSI HL1) when low≤BB lower and RSI<45; exit BB middle only.
- hypers: pattern=micro_ll_hl1_touch_lower, exit=bb_mid_only, rsi_cap=45
- W1 2026-06-30~2026-07-29: return -5.82%, PF 1.41, trades 89, trades/day ≈2.97, fees on
- W2 2026-05-31~2026-06-29: return -18.23%, PF 0.73, trades 129, trades/day ≈4.3, fees on
- W3 2026-05-01~2026-05-30: return -12.56%, PF 0.69, trades 91, trades/day ≈3.03, fees on
- bar A: FAIL (0/3 net>0)
- bar B: FAIL (no passing window; max tpd≈4.3)
- bar C: FAIL (worst -18.23%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: OR reclaim(cross_above lower+RSI HL1 RSI<45) / soft LL/HL2@lower exit mid/RSI60 — v49 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v49.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +1.79%
Total Return -5.82%
CAGR        -52.99%
MDD         -6.29%
Sharpe      -6.53  (Rf=0, portfolio / full equity curve)
Sharpe      11.69  (Rf=0, trades / position holding periods only)
Trades      89  Win Rate 79% (before fees)
Profit Factor  1.41 (before fees)
SL 6 / TP 0 / sell 83 / final_bar 0
Total Fees  87,353
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -17.77%
Total Return -18.23%
CAGR        -92.06%
MDD         -19.10%
Sharpe      -11.69  (Rf=0, portfolio / full equity curve)
Sharpe      -11.07  (Rf=0, trades / position holding periods only)
Trades      129  Win Rate 60% (before fees)
Profit Factor  0.73 (before fees)
SL 31 / TP 0 / sell 98 / final_bar 0
Total Fees  113,177
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.56%
Total Return -12.56%
CAGR        -81.53%
MDD         -13.27%
Sharpe      -14.74  (Rf=0, portfolio / full equity curve)
Sharpe      -12.13  (Rf=0, trades / position holding periods only)
Trades      91  Win Rate 64% (before fees)
Profit Factor  0.69 (before fees)
SL 13 / TP 0 / sell 77 / final_bar 1
Total Fees  86,453
```
