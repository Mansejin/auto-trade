# v47 FAIL

- slug: `daytrade-bb-rsi-div-v47`
- hypothesis: BTC daytrade long-only: classic bull (low LL10 + RSI HL10) + green close at/below BB lower; exit BB mid or RSI≥55.
- hypers: pattern=classic_ll_hl10_green_at_lower, exit=bb_mid_or_rsi55, div_lookback=10
- W1 2026-06-30~2026-07-29: return -0.01%, PF ∞, trades 1, trades/day ≈0.03, fees on
- W2 2026-05-31~2026-06-29: return -0.33%, PF 0.00, trades 1, trades/day ≈0.03, fees on
- W3 2026-05-01~2026-05-30: return +0.03%, PF ∞, trades 1, trades/day ≈0.03, fees on
- bar A: FAIL (1/3 net>0)
- bar B: FAIL (passing W3 tpd≈0.03 < 5.0)
- bar C: PASS (worst -0.33%)
- bar D: PASS
- bar E: PASS
- deploy_status: none
- next_action: micro LL/HL1 touch BB lower RSI<45 exit mid only — v48 백테스트.
- staged: `strategies/daytrade-bb-rsi-div-v48.json` validate OK

### W1 stdout
```
Period      2026-06-30 ~ 2026-07-29 (UTC) (trading bars: 8296, warmup bars: 32)
Benchmark   +1.79%
Total Return -0.01%
CAGR        -0.07%
MDD         -0.14%
Sharpe      -0.10  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,000
```

### W2 stdout
```
Period      2026-05-31 ~ 2026-06-29 (UTC) (trading bars: 8353, warmup bars: 32)
Benchmark   -17.77%
Total Return -0.33%
CAGR        -4.02%
MDD         -0.43%
Sharpe      -3.65  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  998
```

### W3 stdout
```
Period      2026-05-01 ~ 2026-05-30 (UTC) (trading bars: 8353, warmup bars: 32)
Benchmark   -4.56%
Total Return +0.03%
CAGR        +0.33%
MDD         -0.16%
Sharpe      0.46  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  1,000
```
