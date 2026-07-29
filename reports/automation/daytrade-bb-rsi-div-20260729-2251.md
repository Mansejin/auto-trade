# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 22:51 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v32`
- 가설: BTC daytrade long-only: close cross_above BB lower + RSI↑1 + RSI<50; exit BB upper or RSI≥70.
- hypers: pattern=bb_lower_reclaim_cross_rsi_up_rsi_lt50, exit=bb_upper_or_rsi70, div_lookback=0
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -4.83%
CAGR        -46.38%
MDD         -7.72%
Sharpe      -3.06  (Rf=0, portfolio / full equity curve)
Sharpe      6.69  (Rf=0, trades / position holding periods only)
Trades      109  Win Rate 70% (before fees)
Profit Factor  1.33 (before fees)
SL 20 / TP 0 / sell 88 / final_bar 1
Total Fees  108,204
```
- trades/day ≈ 109/30 ≈ 3.63

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -13.68%
CAGR        -84.31%
MDD         -17.02%
Sharpe      -5.54  (Rf=0, portfolio / full equity curve)
Sharpe      -0.48  (Rf=0, trades / position holding periods only)
Trades      135  Win Rate 51% (before fees)
Profit Factor  0.96 (before fees)
SL 52 / TP 2 / sell 80 / final_bar 1
Total Fees  119,872
```
- trades/day ≈ 135/30 ≈ 4.50

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return -11.95%
CAGR        -79.86%
MDD         -15.24%
Sharpe      -8.79  (Rf=0, portfolio / full equity curve)
Sharpe      -2.07  (Rf=0, trades / position holding periods only)
Trades      108  Win Rate 65% (before fees)
Profit Factor  0.92 (before fees)
SL 22 / TP 0 / sell 86 / final_bar 0
Total Fees  104,487
```
- trades/day ≈ 108/30 ≈ 3.60

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net−; W1만 PF1.33 but net−4.83%) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 전체 3.63/4.50/3.60 <5) |
| C worst net ≥ −2% | FAIL (worst Total Return -13.68%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v33` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: BB lower reclaim cross+RSI↑1 RSI<50 제거 → soft bull div(price↓5 RSI↑5) + RSI<40 + close<BB mid; 청산 BB upper or RSI≥70
- next_action: soft bull div5 + RSI<40 below mid → upper/RSI70 — v33 백테스트.
