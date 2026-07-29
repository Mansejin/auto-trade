# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 22:11 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v28`
- 가설: BTC daytrade long-only: green lower reclaim (low≤BB lower, close>lower, close>open) with RSI>rsi_signal; exit BB upper or RSI≥65.
- hypers: pattern=green_lower_reclaim_rsi_gt_signal, exit=bb_upper_or_rsi65, confirm=close_gt_open
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return -4.60%
CAGR        -44.73%
MDD         -7.21%
Sharpe      -4.37  (Rf=0, portfolio / full equity curve)
Sharpe      3.57  (Rf=0, trades / position holding periods only)
Trades      61  Win Rate 70% (before fees)
Profit Factor  1.15 (before fees)
SL 10 / TP 0 / sell 51 / final_bar 0
Total Fees  59,272
```
- trades/day ≈ 61/30 ≈ 2.03

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -15.54%
CAGR        -88.06%
MDD         -17.45%
Sharpe      -9.88  (Rf=0, portfolio / full equity curve)
Sharpe      -11.39  (Rf=0, trades / position holding periods only)
Trades      79  Win Rate 48% (before fees)
Profit Factor  0.67 (before fees)
SL 35 / TP 2 / sell 42 / final_bar 0
Total Fees  70,182
```
- trades/day ≈ 79/30 ≈ 2.63

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -2.68%
CAGR        -28.98%
MDD         -4.99%
Sharpe      -2.85  (Rf=0, portfolio / full equity curve)
Sharpe      9.93  (Rf=0, trades / position holding periods only)
Trades      66  Win Rate 79% (before fees)
Profit Factor  1.48 (before fees)
SL 9 / TP 0 / sell 57 / final_bar 0
Total Fees  66,277
```
- trades/day ≈ 66/30 ≈ 2.20

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; nets -4.60/-15.54/-2.68%; W3만 PF 1.48이나 net≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 2.03/2.63/2.20) |
| C worst net ≥ −2% | FAIL (worst Total Return -15.54%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v29` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: green lower reclaim 제거 → RSI signal bull cross + soft bull div(lookback6) below BB mid, 청산 BB upper only (RSI 청산 제거·수수료 재진입 억제)
- next_action: RSI signal cross + soft div6 below mid → upper only — v29 백테스트.
