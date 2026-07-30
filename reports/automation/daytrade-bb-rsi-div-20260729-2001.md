# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 20:01 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v15`
- 가설: BTC daytrade long-only: while close stays above BB mid, low tags BB mid (mid-support bounce) with RSI>45 and RSI>rsi_signal; exit BB upper or RSI≥70.
- hypers: pattern=mid_support_bounce, rsi_floor=45, exit=bb_upper_or_rsi70
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return -12.97%
CAGR        -82.59%
MDD         -13.22%
Sharpe      -10.53  (Rf=0, portfolio / full equity curve)
Sharpe      -0.31  (Rf=0, trades / position holding periods only)
Trades      136  Win Rate 72% (before fees)
Profit Factor  0.99 (before fees)
SL 18 / TP 0 / sell 118 / final_bar 0
Total Fees  127,920
```
- trades/day ≈ 136/30 ≈ 4.53

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -20.20%
CAGR        -94.16%
MDD         -20.32%
Sharpe      -13.06  (Rf=0, portfolio / full equity curve)
Sharpe      -11.70  (Rf=0, trades / position holding periods only)
Trades      125  Win Rate 58% (before fees)
Profit Factor  0.67 (before fees)
SL 37 / TP 0 / sell 87 / final_bar 1
Total Fees  108,517
```
- trades/day ≈ 125/30 ≈ 4.17

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -11.40%
CAGR        -78.21%
MDD         -12.90%
Sharpe      -10.79  (Rf=0, portfolio / full equity curve)
Sharpe      -1.70  (Rf=0, trades / position holding periods only)
Trades      110  Win Rate 69% (before fees)
Profit Factor  0.93 (before fees)
SL 14 / TP 0 / sell 96 / final_bar 0
Total Fees  105,037
```
- trades/day ≈ 110/30 ≈ 3.67

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net≤0; PF 전부 <1.2) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 전부 <5) |
| C worst net ≥ −2% | FAIL (worst Total Return -20.20%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v16` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: mid-support bounce 제거 → BB mid 상승(mid>mid[5]) 추세 필터 + BB lower 터치·종가 복귀 + RSI<40, 청산 BB mid/RSI60
- next_action: BB mid 상승 필터 + lower tag/reclaim + RSI<40 → mid/RSI60 — v16 백테스트.
