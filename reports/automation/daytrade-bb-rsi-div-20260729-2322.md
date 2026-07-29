# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 23:22 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v35`
- 가설: BTC daytrade long-only: hidden bull div (price HL3 + RSI LL3) at/below BB lower; exit BB upper or RSI≥65.
- hypers: pattern=hidden_hl_ll3_at_bb_lower, exit=bb_upper_or_rsi65, div_lookback=3
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 25)
Benchmark   +3.26%
Total Return -0.04%
CAGR        -0.49%
MDD         -0.80%
Sharpe      -0.13  (Rf=0, portfolio / full equity curve)
Sharpe      12.28  (Rf=0, trades / position holding periods only)
Trades      3  Win Rate 33% (before fees)
Profit Factor  2.18 (before fees)
SL 0 / TP 0 / sell 3 / final_bar 0
Total Fees  3,005
```
- trades/day ≈ 3/30 ≈ 0.10

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -16.19%
Total Return +0.05%
CAGR        +0.69%
MDD         -1.39%
Sharpe      0.20  (Rf=0, portfolio / full equity curve)
Sharpe      10.82  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 75% (before fees)
Profit Factor  1.57 (before fees)
SL 1 / TP 0 / sell 3 / final_bar 0
Total Fees  3,989
```
- trades/day ≈ 4/30 ≈ 0.13

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -4.12%
Total Return +0.12%
CAGR        +1.57%
MDD         -0.66%
Sharpe      0.69  (Rf=0, portfolio / full equity curve)
Sharpe      39.23  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 75% (before fees)
Profit Factor  4.69 (before fees)
SL 0 / TP 0 / sell 4 / final_bar 0
Total Fees  3,998
```
- trades/day ≈ 4/30 ≈ 0.13

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | PASS (2/3; W2/W3 net+ PF 1.57/4.69; W1 net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 W2/W3 모두 0.13 <5) |
| C worst net ≥ −2% | PASS (worst Total Return -0.04%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v36` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: hidden HL/LL3 at lower 제거 → soft classic bull(close LL2 + RSI HL2) below BB mid + RSI<50; 청산 BB upper or RSI≥60
- next_action: soft classic LL/HL2 below BB mid RSI<50 → upper/RSI60 — v36 백테스트.
