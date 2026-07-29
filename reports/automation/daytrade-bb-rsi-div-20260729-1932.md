# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 19:32 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v12`
- 가설: BTC daytrade long-only: prior close≤BB mid then reclaim above mid, prior RSI<40 and RSI rising 1 bar; exit BB upper or RSI≥65.
- hypers: pattern=mid_reclaim, rsi_prior_cap=40, exit=bb_upper_or_rsi65
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -1.40%
CAGR        -16.29%
MDD         -2.87%
Sharpe      -2.22  (Rf=0, portfolio / full equity curve)
Sharpe      11.00  (Rf=0, trades / position holding periods only)
Trades      29  Win Rate 79% (before fees)
Profit Factor  1.43 (before fees)
SL 4 / TP 0 / sell 25 / final_bar 0
Total Fees  28,541
```
- trades/day ≈ 29/30 ≈ 0.97

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -4.22%
CAGR        -41.87%
MDD         -4.89%
Sharpe      -5.56  (Rf=0, portfolio / full equity curve)
Sharpe      -5.96  (Rf=0, trades / position holding periods only)
Trades      32  Win Rate 69% (before fees)
Profit Factor  0.82 (before fees)
SL 7 / TP 0 / sell 25 / final_bar 0
Total Fees  30,943
```
- trades/day ≈ 32/30 ≈ 1.07

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return -2.42%
CAGR        -26.52%
MDD         -3.55%
Sharpe      -3.57  (Rf=0, portfolio / full equity curve)
Sharpe      10.98  (Rf=0, trades / position holding periods only)
Trades      42  Win Rate 81% (before fees)
Profit Factor  1.46 (before fees)
SL 4 / TP 0 / sell 38 / final_bar 0
Total Fees  41,968
```
- trades/day ≈ 42/30 ≈ 1.40

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 전부 ≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -4.22%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v13` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: OS mid-reclaim 제거 → BB mid cross + RSI>50·RSI>rsi_signal 불 연속, 청산 BB upper/RSI70
- next_action: BB mid cross + RSI>50·RSI>signal → upper/RSI70 — v13 백테스트.
