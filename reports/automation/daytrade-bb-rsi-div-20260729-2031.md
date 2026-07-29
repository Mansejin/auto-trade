# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 20:31 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v18`
- 가설: BTC daytrade long-only: while close < BB mid, RSI flips above 50 (prior ≤50); fade to BB mid or RSI≥60.
- hypers: pattern=rsi50_cross_below_mid_fade, rsi_flip=50, exit=bb_mid_or_rsi60
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -11.76%
CAGR        -79.30%
MDD         -11.79%
Sharpe      -17.75  (Rf=0, portfolio / full equity curve)
Sharpe      -21.04  (Rf=0, trades / position holding periods only)
Trades      83  Win Rate 63% (before fees)
Profit Factor  0.57 (before fees)
SL 9 / TP 0 / sell 74 / final_bar 0
Total Fees  78,090
```
- trades/day ≈ 83/30 ≈ 2.77

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -9.23%
CAGR        -70.45%
MDD         -9.34%
Sharpe      -10.91  (Rf=0, portfolio / full equity curve)
Sharpe      -1.59  (Rf=0, trades / position holding periods only)
Trades      93  Win Rate 74% (before fees)
Profit Factor  0.96 (before fees)
SL 10 / TP 0 / sell 83 / final_bar 0
Total Fees  88,867
```
- trades/day ≈ 93/30 ≈ 3.10

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return -5.46%
CAGR        -50.67%
MDD         -5.64%
Sharpe      -11.78  (Rf=0, portfolio / full equity curve)
Sharpe      27.58  (Rf=0, trades / position holding periods only)
Trades      79  Win Rate 73% (before fees)
Profit Factor  1.90 (before fees)
SL 0 / TP 0 / sell 79 / final_bar 0
Total Fees  76,792
```
- trades/day ≈ 79/30 ≈ 2.63

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; all Total Return < 0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 2.77/3.10/2.63≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -11.76%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v19` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: RSI50 flip fade 제거 → BB 밴드 확장(upper>upper[8] & lower<lower[8]) + close cross_above BB mid + RSI>rsi_signal, 청산 BB upper/RSI70
- next_action: BB expand(lookback8) + mid cross_above + RSI>signal → upper/RSI70 — v19 백테스트.
