# v1 PASS

- slug: `daytrade-edge-15m-div-v1`
- hypothesis: BTC daytrade: 15m hidden bull div (HL + RSI LL3) at BB lower → long; exit BB upper only.
- hypers: tf=15m, div_lookback=3, exit=bb_upper_only
- fail_mode: null (PASS)
- W1 2026-06-30~2026-07-29: return -0.21%, PF 0.00, trades 1, trades/day 0.03, fees on
- W2 2026-05-31~2026-06-29: return +0.39%, PF ∞, trades 1, trades/day 0.03, fees on
- W3 2026-05-01~2026-05-30: return +1.33%, PF ∞, trades 2, trades/day 0.07, fees on
- bar A: PASS (2/3 net>0 with PF≥1.2 or zero-loss)
- bar B: PASS (worst -0.21% ≥ −2%)
- bar C: PASS
- bar D: PASS
- ledger.next_priority: FREEZE daytrade-edge-15m-div-v1; retry bot deploy when AUTO_TRADE_BOT_SSH_KEY present. Do not encode new card until deploy succeeds or live evidence demands two-sided 15m.
- deploy_status: failed (AUTO_TRADE_BOT_SSH_KEY unset)

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 2767, warmup bars: 25)
Benchmark   +1.85%
Total Return -0.21%
CAGR        -2.59%
MDD         -0.87%
Sharpe      -1.14  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  999
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -17.47%
Total Return +0.39%
CAGR        +4.96%
MDD         -0.73%
Sharpe      1.72  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,002
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 2785, warmup bars: 25)
Benchmark   -4.49%
Total Return +1.33%
CAGR        +18.11%
MDD         -0.50%
Sharpe      4.63  (Rf=0, portfolio / full equity curve)
Sharpe      30.98  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 2 / final_bar 0
Total Fees  2,008
```
