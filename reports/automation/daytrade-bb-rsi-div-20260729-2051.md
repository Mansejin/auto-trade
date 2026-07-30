# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 20:51 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v20`
- 가설: BTC daytrade long-only: BB squeeze vs 12 bars ago (upper↓ & lower↑) and close cross_above BB mid with RSI>50; ride to BB upper or RSI≥70.
- hypers: pattern=bb_squeeze_mid_cross, squeeze_lookback=12, exit=bb_upper_or_rsi70
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 32)
Benchmark   +3.26%
Total Return -7.95%
CAGR        -64.72%
MDD         -7.95%
Sharpe      -7.65  (Rf=0, portfolio / full equity curve)
Sharpe      0.89  (Rf=0, trades / position holding periods only)
Trades      86  Win Rate 76% (before fees)
Profit Factor  1.02 (before fees)
SL 13 / TP 0 / sell 73 / final_bar 0
Total Fees  81,748
```
- trades/day ≈ 86/30 ≈ 2.87

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 32)
Benchmark   -16.19%
Total Return -11.23%
CAGR        -77.68%
MDD         -11.32%
Sharpe      -8.01  (Rf=0, portfolio / full equity curve)
Sharpe      -5.73  (Rf=0, trades / position holding periods only)
Trades      83  Win Rate 61% (before fees)
Profit Factor  0.81 (before fees)
SL 23 / TP 1 / sell 59 / final_bar 0
Total Fees  77,254
```
- trades/day ≈ 83/30 ≈ 2.77

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 32)
Benchmark   -4.12%
Total Return -10.68%
CAGR        -75.85%
MDD         -11.01%
Sharpe      -11.46  (Rf=0, portfolio / full equity curve)
Sharpe      -9.33  (Rf=0, trades / position holding periods only)
Trades      74  Win Rate 64% (before fees)
Profit Factor  0.64 (before fees)
SL 10 / TP 0 / sell 64 / final_bar 0
Total Fees  69,955
```
- trades/day ≈ 74/30 ≈ 2.47

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; all Total Return < 0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 2.87/2.77/2.47≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -11.23%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v21` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: BB squeeze mid-cross 제거 → soft bull div(close<close[8] & RSI>RSI[8]) + RSI45 reclaim(prior<45→≥45) under BB mid, 청산 BB upper/RSI65
- next_action: soft bull div(lookback8) + RSI45 reclaim under BB mid → upper/RSI65 — v21 백테스트.
