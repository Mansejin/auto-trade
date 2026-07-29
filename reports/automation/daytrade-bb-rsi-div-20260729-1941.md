# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 19:41 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v13`
- 가설: BTC daytrade long-only: prior close≤BB mid then reclaim above mid with RSI>50 and RSI>rsi_signal (bull continuation); exit BB upper or RSI≥70.
- hypers: pattern=mid_cross_bull_cont, rsi_floor=50, exit=bb_upper_or_rsi70
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return -15.90%
CAGR        -88.69%
MDD         -15.90%
Sharpe      -11.23  (Rf=0, portfolio / full equity curve)
Sharpe      -1.19  (Rf=0, trades / position holding periods only)
Trades      162  Win Rate 72% (before fees)
Profit Factor  0.94 (before fees)
SL 25 / TP 0 / sell 137 / final_bar 0
Total Fees  145,577
```
- trades/day ≈ 162/30 ≈ 5.40

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -17.93%
CAGR        -91.68%
MDD         -18.13%
Sharpe      -9.10  (Rf=0, portfolio / full equity curve)
Sharpe      -3.14  (Rf=0, trades / position holding periods only)
Trades      156  Win Rate 60% (before fees)
Profit Factor  0.88 (before fees)
SL 42 / TP 2 / sell 111 / final_bar 1
Total Fees  139,258
```
- trades/day ≈ 156/30 ≈ 5.20

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -17.51%
CAGR        -91.13%
MDD         -18.61%
Sharpe      -14.68  (Rf=0, portfolio / full equity curve)
Sharpe      -7.71  (Rf=0, trades / position holding periods only)
Trades      134  Win Rate 65% (before fees)
Profit Factor  0.73 (before fees)
SL 19 / TP 0 / sell 115 / final_bar 0
Total Fees  125,932
```
- trades/day ≈ 134/30 ≈ 4.47

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; W1/W2는 ≥5이나 A 미통과) |
| C worst net ≥ −2% | FAIL (worst Total Return -17.93%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v14` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: mid-cross 불연속 제거 → BB upper breakout + RSI>55·RSI>signal, 청산 BB mid/RSI45
- next_action: BB upper breakout + RSI>55·RSI>signal → mid/RSI45 — v14 백테스트.
