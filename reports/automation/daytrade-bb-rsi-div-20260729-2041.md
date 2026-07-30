# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 20:41 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v19`
- 가설: BTC daytrade long-only: BB expands vs 8 bars ago (upper↑ & lower↓) and close cross_above BB mid with RSI>rsi_signal; ride to BB upper or RSI≥70.
- hypers: pattern=bb_expand_mid_cross, expand_lookback=8, exit=bb_upper_or_rsi70
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 28)
Benchmark   +3.26%
Total Return -2.90%
CAGR        -30.95%
MDD         -4.64%
Sharpe      -3.78  (Rf=0, portfolio / full equity curve)
Sharpe      3.07  (Rf=0, trades / position holding periods only)
Trades      36  Win Rate 64% (before fees)
Profit Factor  1.11 (before fees)
SL 6 / TP 0 / sell 30 / final_bar 0
Total Fees  35,270
```
- trades/day ≈ 36/30 ≈ 1.20

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 28)
Benchmark   -16.19%
Total Return -5.55%
CAGR        -51.28%
MDD         -7.10%
Sharpe      -5.89  (Rf=0, portfolio / full equity curve)
Sharpe      -7.56  (Rf=0, trades / position holding periods only)
Trades      35  Win Rate 54% (before fees)
Profit Factor  0.75 (before fees)
SL 10 / TP 0 / sell 25 / final_bar 0
Total Fees  33,743
```
- trades/day ≈ 35/30 ≈ 1.17

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 28)
Benchmark   -4.12%
Total Return -4.92%
CAGR        -47.02%
MDD         -5.64%
Sharpe      -7.05  (Rf=0, portfolio / full equity curve)
Sharpe      -7.99  (Rf=0, trades / position holding periods only)
Trades      33  Win Rate 58% (before fees)
Profit Factor  0.71 (before fees)
SL 6 / TP 0 / sell 27 / final_bar 0
Total Fees  32,621
```
- trades/day ≈ 33/30 ≈ 1.10

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; all Total Return < 0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 1.20/1.17/1.10≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -5.55%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v20` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: BB expand 제거 → BB squeeze(upper↓&lower↑ vs lookback12) + close cross_above BB mid + RSI>50, 청산 BB upper/RSI70
- next_action: BB squeeze(lookback12) + mid cross_above + RSI>50 → upper/RSI70 — v20 백테스트.
