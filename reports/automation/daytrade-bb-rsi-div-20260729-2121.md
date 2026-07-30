# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 21:21 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v23`
- 가설: BTC daytrade long-only: BB lower reclaim with soft bullish divergence — prior close ≤ BB lower then close > lower, while close < close[5] and RSI > RSI[5]; ride to BB upper or RSI≥60.
- hypers: pattern=lower_reclaim_soft_div5, div_lookback=5, exit=bb_upper_or_rsi60
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 27)
Benchmark   +3.26%
Total Return -0.72%
CAGR        -8.74%
MDD         -2.04%
Sharpe      -0.95  (Rf=0, portfolio / full equity curve)
Sharpe      10.65  (Rf=0, trades / position holding periods only)
Trades      28  Win Rate 71% (before fees)
Profit Factor  1.58 (before fees)
SL 4 / TP 0 / sell 24 / final_bar 0
Total Fees  28,039
```
- trades/day ≈ 28/30 ≈ 0.93

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -16.19%
Total Return -8.38%
CAGR        -66.78%
MDD         -9.24%
Sharpe      -7.19  (Rf=0, portfolio / full equity curve)
Sharpe      -12.62  (Rf=0, trades / position holding periods only)
Trades      37  Win Rate 41% (before fees)
Profit Factor  0.66 (before fees)
SL 18 / TP 2 / sell 17 / final_bar 0
Total Fees  35,132
```
- trades/day ≈ 37/30 ≈ 1.23

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -4.12%
Total Return -3.18%
CAGR        -33.39%
MDD         -4.80%
Sharpe      -4.39  (Rf=0, portfolio / full equity curve)
Sharpe      -0.90  (Rf=0, trades / position holding periods only)
Trades      30  Win Rate 67% (before fees)
Profit Factor  0.97 (before fees)
SL 6 / TP 0 / sell 24 / final_bar 0
Total Fees  30,017
```
- trades/day ≈ 30/30 ≈ 1.00

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; W1 -0.72%/PF1.58, W2 -8.38%/PF0.66, W3 -3.18%/PF0.97) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 0.93/1.23/1.00≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -8.38%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v24` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: lower reclaim+soft div5 제거 → BB mid 아래 1-bar soft bull div(close<close[1] & RSI>RSI[1]), 청산 BB mid/RSI50 (빈도↑ 목적)
- next_action: under BB mid + 1-bar soft div → mid/RSI50 — v24 백테스트.
