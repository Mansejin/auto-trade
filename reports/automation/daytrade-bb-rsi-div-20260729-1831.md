# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 18:31 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v6`
- 가설: BTC daytrade long-only: close cross_above BB lower AND RSI cross_above rsi_signal (reclaim+turn), ride to BB upper or RSI≥65 (not mid fade).
- hypers: entry=bb_lower_reclaim+rsi_signal_cross, exit_band=bb_upper, rsi_exit=65
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return -6.21%
CAGR        -55.37%
MDD         -7.31%
Sharpe      -6.74  (Rf=0, portfolio / full equity curve)
Sharpe      -5.59  (Rf=0, trades / position holding periods only)
Trades      43  Win Rate 58% (before fees)
Profit Factor  0.79 (before fees)
SL 11 / TP 0 / sell 32 / final_bar 0
Total Fees  41,788
```
- trades/day ≈ 43/30 ≈ 1.43 (바 B 미달)

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -15.99%
CAGR        -88.84%
MDD         -17.20%
Sharpe      -11.73  (Rf=0, portfolio / full equity curve)
Sharpe      -17.82  (Rf=0, trades / position holding periods only)
Trades      64  Win Rate 47% (before fees)
Profit Factor  0.52 (before fees)
SL 29 / TP 1 / sell 34 / final_bar 0
Total Fees  56,512
```
- trades/day ≈ 64/30 ≈ 2.13 (바 B 미달)

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -0.97%
CAGR        -11.57%
MDD         -4.54%
Sharpe      -1.01  (Rf=0, portfolio / full equity curve)
Sharpe      13.26  (Rf=0, trades / position holding periods only)
Trades      54  Win Rate 81% (before fees)
Profit Factor  1.76 (before fees)
SL 7 / TP 0 / sell 47 / final_bar 0
Total Fees  54,885
```
- trades/day ≈ 54/30 ≈ 1.80 (바 B 미달; W3만 PF≥1.2이나 net≤0)

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; W3 PF 1.76 but Total Return -0.97%) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 1.43/2.13/1.80) |
| C worst net ≥ −2% | FAIL (worst Total Return -15.99%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v7` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: BB lower reclaim 제거 → close < BB mid + RSI/signal cross(OS캡 없음), 청산 BB upper/RSI70
- next_action: BB mid 아래 RSI/signal cross(OS캡 제거) → BB upper/RSI70 라이드 — v7 백테스트.
