# daytrade-bb-rsi-div 런 리포트 — 2026-07-30 00:51 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v44`
- 가설: BTC daytrade long-only: close≤BB lower with RSI rising (rsi>rsi[1]) and RSI<40; exit BB upper or RSI≥65.
- hypers: pattern=close_at_lower_rsi_rising, exit=bb_upper_or_rsi65, rsi_cap=40
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -3.62%
CAGR        -37.14%
MDD         -5.73%
Sharpe      -4.43  (Rf=0, portfolio / full equity curve)
Sharpe      -4.44  (Rf=0, trades / position holding periods only)
Trades      25  Win Rate 64% (before fees)
Profit Factor  0.81 (before fees)
SL 8 / TP 0 / sell 17 / final_bar 0
Total Fees  24,236
```
- trades/day ≈ 25/30 ≈ 0.83

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return +1.49%
CAGR        +20.39%
MDD         -4.70%
Sharpe      1.16  (Rf=0, portfolio / full equity curve)
Sharpe      10.43  (Rf=0, trades / position holding periods only)
Trades      37  Win Rate 57% (before fees)
Profit Factor  1.55 (before fees)
SL 11 / TP 1 / sell 25 / final_bar 0
Total Fees  37,026
```
- trades/day ≈ 37/30 ≈ 1.23

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return -3.34%
CAGR        -34.76%
MDD         -4.81%
Sharpe      -4.42  (Rf=0, portfolio / full equity curve)
Sharpe      -1.92  (Rf=0, trades / position holding periods only)
Trades      29  Win Rate 55% (before fees)
Profit Factor  0.92 (before fees)
SL 6 / TP 0 / sell 23 / final_bar 0
Total Fees  28,876
```
- trades/day ≈ 29/30 ≈ 0.97

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (1/3; W2만 +1.49% PF1.55) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 W2 ≈1.23 ≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -3.62%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v45` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: close≤lower+RSI rising→upper/RSI65 제거 → RSI leave-OS30 while close≤BB middle; 청산 BB upper or RSI≥60 (lower 터치 필수 해제해 빈도↑, mid 청산 없음)
- next_action: leave-OS30 + close≤BB mid → upper/RSI60 — v45 백테스트.
