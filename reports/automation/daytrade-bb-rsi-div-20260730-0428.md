# atr-or-v1 PASS

- slug: `daytrade-edge-15m-div-atr-or-v1`
- hypothesis: BTC 15m classic+hidden OR (HL/LL3 RSI) @ BB lower with ATR expanding (atr14 > atr offset 3) → long; exit BB upper only.
- hypers: tf=15m, div_lookback=3, atr_expand_lookback=3
- fail_mode: PASS
- W1 2026-06-30~2026-07-29: return -1.14%, PF 0.57, trades 4, trades/day 0.13, fees on
- W2 2026-05-31~2026-06-29: return +0.77%, PF 2.34, trades 3, trades/day 0.10, fees on
- W3 2026-05-01~2026-05-30: return +2.41%, PF ∞, trades 4, trades/day 0.13, fees on
- bar A: PASS (2/3: W2 +0.77% PF2.34, W3 +2.41% PF∞; W1 net≤0)
- bar B: PASS (worst −1.14% ≥ −2%)
- bar C: PASS
- bar D: PASS
- deploy_status: skipped_no_deploy
- ledger.next_priority: Encode daytrade-edge-15m-div-atr-adx-v1: ADX<25 + ATR expand (atr14 > atr offset 3) + classic+hidden OR @ BB lower → BB upper. No deploy. Keep promoted cards frozen.

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 2767, warmup bars: 25)
Benchmark   +1.85%
Total Return -1.14%
CAGR        -13.46%
MDD         -2.10%
Sharpe      -3.13  (Rf=0, portfolio / full equity curve)
Sharpe      -11.79  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 25% (before fees)
Profit Factor  0.57 (before fees)
SL 2 / TP 0 / sell 2 / final_bar 0
Total Fees  4,007
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -17.47%
Total Return +0.77%
CAGR        +10.20%
MDD         -0.90%
Sharpe      2.12  (Rf=0, portfolio / full equity curve)
Sharpe      15.82  (Rf=0, trades / position holding periods only)
Trades      3  Win Rate 67% (before fees)
Profit Factor  2.34 (before fees)
SL 1 / TP 0 / sell 2 / final_bar 0
Total Fees  2,999
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -4.49%
Total Return +2.41%
CAGR        +35.00%
MDD         -0.50%
Sharpe      6.55  (Rf=0, portfolio / full equity curve)
Sharpe      51.54  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 4 / final_bar 0
Total Fees  4,029
```
