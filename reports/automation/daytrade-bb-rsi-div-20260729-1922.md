# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 19:22 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v11`
- 가설: BTC daytrade long-only: prior bar close≤BB lower then current close>BB lower (tag-then-reclaim), RSI rising 1 bar and RSI<50; exit BB mid or RSI≥55.
- hypers: pattern=tag_reclaim, rsi_cap=50, exit=bb_mid_or_rsi55
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -9.59%
CAGR        -71.88%
MDD         -11.50%
Sharpe      -8.89  (Rf=0, portfolio / full equity curve)
Sharpe      10.29  (Rf=0, trades / position holding periods only)
Trades      147  Win Rate 73% (before fees)
Profit Factor  1.35 (before fees)
SL 12 / TP 0 / sell 134 / final_bar 1
Total Fees  143,828
```
- trades/day ≈ 147/30 ≈ 4.90

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -21.86%
CAGR        -95.51%
MDD         -22.98%
Sharpe      -12.71  (Rf=0, portfolio / full equity curve)
Sharpe      -8.24  (Rf=0, trades / position holding periods only)
Trades      173  Win Rate 60% (before fees)
Profit Factor  0.79 (before fees)
SL 40 / TP 2 / sell 130 / final_bar 1
Total Fees  149,388
```
- trades/day ≈ 173/30 ≈ 5.77

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return -15.47%
CAGR        -87.95%
MDD         -16.74%
Sharpe      -15.55  (Rf=0, portfolio / full equity curve)
Sharpe      -6.94  (Rf=0, trades / position holding periods only)
Trades      135  Win Rate 59% (before fees)
Profit Factor  0.81 (before fees)
SL 13 / TP 0 / sell 122 / final_bar 0
Total Fees  126,104
```
- trades/day ≈ 135/30 ≈ 4.50

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; W2만 5.77이지만 net<0) |
| C worst net ≥ −2% | FAIL (worst Total Return -21.86%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v12` (JSON 저장·validate 예정, 백테스트는 다음 런)
- 구조 변경: BB lower tag-reclaim 제거 → BB mid tag-then-reclaim + prior RSI<40·RSI↑1, 청산 BB upper/RSI65
- next_action: BB mid tag-then-reclaim + prior RSI<40 RSI↑1 → upper/RSI65 — v12 백테스트.
