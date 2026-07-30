# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 21:02 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v21`
- 가설: BTC daytrade long-only: soft bullish divergence under BB mid — close < close[8] while RSI > RSI[8], then RSI reclaim ≥45 from prior <45; ride to BB upper or RSI≥65.
- hypers: pattern=soft_bull_div_rsi45_reclaim, div_lookback=8, exit=bb_upper_or_rsi65
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 30)
Benchmark   +3.26%
Total Return -1.41%
CAGR        -16.32%
MDD         -3.95%
Sharpe      -1.42  (Rf=0, portfolio / full equity curve)
Sharpe      12.54  (Rf=0, trades / position holding periods only)
Trades      52  Win Rate 77% (before fees)
Profit Factor  1.64 (before fees)
SL 6 / TP 0 / sell 46 / final_bar 0
Total Fees  51,301
```
- trades/day ≈ 52/30 ≈ 1.73

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 30)
Benchmark   -16.19%
Total Return -7.39%
CAGR        -61.97%
MDD         -9.29%
Sharpe      -6.57  (Rf=0, portfolio / full equity curve)
Sharpe      -5.71  (Rf=0, trades / position holding periods only)
Trades      51  Win Rate 57% (before fees)
Profit Factor  0.80 (before fees)
SL 16 / TP 0 / sell 35 / final_bar 0
Total Fees  47,786
```
- trades/day ≈ 51/30 ≈ 1.70

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 30)
Benchmark   -4.12%
Total Return -1.95%
CAGR        -21.95%
MDD         -3.15%
Sharpe      -2.93  (Rf=0, portfolio / full equity curve)
Sharpe      9.20  (Rf=0, trades / position holding periods only)
Trades      40  Win Rate 80% (before fees)
Profit Factor  1.40 (before fees)
SL 6 / TP 0 / sell 34 / final_bar 0
Total Fees  39,778
```
- trades/day ≈ 40/30 ≈ 1.33

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; all Total Return < 0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 1.73/1.70/1.33≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -7.39%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v22` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: soft bull div + RSI45 reclaim 제거 → classic LL/HL (low<low[10] & RSI>RSI[10]) at close≤BB lower, 청산 BB mid/RSI55
- next_action: classic LL/HL div(lookback10) at BB lower → mid/RSI55 — v22 백테스트.
