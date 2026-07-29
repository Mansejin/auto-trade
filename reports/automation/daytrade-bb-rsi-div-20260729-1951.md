# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 19:51 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v14`
- 가설: BTC daytrade long-only: prior close≤BB upper then reclaim above upper with RSI>55 and RSI>rsi_signal (upper-band breakout continuation); exit BB mid or RSI≤45.
- hypers: pattern=upper_breakout, rsi_floor=55, exit=bb_mid_or_rsi45
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return -17.07%
CAGR        -90.52%
MDD         -17.63%
Sharpe      -13.24  (Rf=0, portfolio / full equity curve)
Sharpe      -4.32  (Rf=0, trades / position holding periods only)
Trades      158  Win Rate 35% (before fees)
Profit Factor  0.85 (before fees)
SL 1 / TP 1 / sell 156 / final_bar 0
Total Fees  146,041
```
- trades/day ≈ 158/30 ≈ 5.27

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -18.26%
CAGR        -92.10%
MDD         -18.39%
Sharpe      -12.14  (Rf=0, portfolio / full equity curve)
Sharpe      -9.38  (Rf=0, trades / position holding periods only)
Trades      136  Win Rate 30% (before fees)
Profit Factor  0.72 (before fees)
SL 7 / TP 1 / sell 128 / final_bar 0
Total Fees  122,467
```
- trades/day ≈ 136/30 ≈ 4.53

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -9.92%
CAGR        -73.16%
MDD         -10.49%
Sharpe      -9.31  (Rf=0, portfolio / full equity curve)
Sharpe      5.58  (Rf=0, trades / position holding periods only)
Trades      129  Win Rate 39% (before fees)
Profit Factor  1.20 (before fees)
SL 1 / TP 0 / sell 128 / final_bar 0
Total Fees  121,761
```
- trades/day ≈ 129/30 ≈ 4.30

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net≤0; W3만 PF 1.20이나 net -9.92%) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; W1만 ≥5) |
| C worst net ≥ −2% | FAIL (worst Total Return -18.26%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v15` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: upper breakout 제거 → BB mid 위 유지 + low가 mid 터치(지지 바운스) + RSI>45·RSI>signal, 청산 BB upper/RSI70
- next_action: BB mid-support bounce(위유지+low터치) + RSI>45·RSI>signal → upper/RSI70 — v15 백테스트.
