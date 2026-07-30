# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 21:11 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v22`
- 가설: BTC daytrade long-only: classic bullish divergence at BB lower — low < low[10] while RSI > RSI[10] and close ≤ BB lower; mean-revert to BB mid or RSI≥55.
- hypers: pattern=classic_ll_hl_div_bb_lower, div_lookback=10, exit=bb_mid_or_rsi55
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 32)
Benchmark   +3.26%
Total Return -0.00%
CAGR        -0.03%
MDD         -0.60%
Sharpe      0.00  (Rf=0, portfolio / full equity curve)
Sharpe      71.27  (Rf=0, trades / position holding periods only)
Trades      7  Win Rate 86% (before fees)
Profit Factor  5.74 (before fees)
SL 0 / TP 0 / sell 7 / final_bar 0
Total Fees  6,990
```
- trades/day ≈ 7/30 ≈ 0.23

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 32)
Benchmark   -16.19%
Total Return -2.16%
CAGR        -24.08%
MDD         -2.53%
Sharpe      -6.35  (Rf=0, portfolio / full equity curve)
Sharpe      -37.50  (Rf=0, trades / position holding periods only)
Trades      8  Win Rate 25% (before fees)
Profit Factor  0.33 (before fees)
SL 2 / TP 0 / sell 6 / final_bar 0
Total Fees  7,884
```
- trades/day ≈ 8/30 ≈ 0.27

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 32)
Benchmark   -4.12%
Total Return +0.40%
CAGR        +5.14%
MDD         -0.38%
Sharpe      2.06  (Rf=0, portfolio / full equity curve)
Sharpe      95.73  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 4 / final_bar 0
Total Fees  4,008
```
- trades/day ≈ 4/30 ≈ 0.13

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (1/3; W3만 +0.40%/PF∞, W1 -0.00%·W2 -2.16%) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 W3만 0.13≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -2.16%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v23` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: classic LL/HL at BB lower 제거 → prior close≤BB lower 후 reclaim + soft bull div(close<close[5] & RSI>RSI[5]), 청산 BB upper/RSI60
- next_action: BB lower reclaim + soft div(lookback5) → upper/RSI60 — v23 백테스트.
