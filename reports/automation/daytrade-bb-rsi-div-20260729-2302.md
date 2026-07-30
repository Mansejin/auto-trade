# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 23:02 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v33`
- 가설: BTC daytrade long-only: soft bull div (price↓5 RSI↑5) + RSI<40 + close<BB mid; exit BB upper or RSI≥70.
- hypers: pattern=softdiv5_rsi_lt40_below_mid, exit=bb_upper_or_rsi70, div_lookback=5
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 27)
Benchmark   +3.26%
Total Return -1.99%
CAGR        -22.37%
MDD         -4.12%
Sharpe      -1.50  (Rf=0, portfolio / full equity curve)
Sharpe      9.72  (Rf=0, trades / position holding periods only)
Trades      73  Win Rate 71% (before fees)
Profit Factor  1.48 (before fees)
SL 12 / TP 0 / sell 60 / final_bar 1
Total Fees  71,963
```
- trades/day ≈ 73/30 ≈ 2.43

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -16.19%
Total Return -3.43%
CAGR        -35.51%
MDD         -11.31%
Sharpe      -1.41  (Rf=0, portfolio / full equity curve)
Sharpe      5.43  (Rf=0, trades / position holding periods only)
Trades      98  Win Rate 60% (before fees)
Profit Factor  1.22 (before fees)
SL 36 / TP 2 / sell 59 / final_bar 1
Total Fees  94,693
```
- trades/day ≈ 98/30 ≈ 3.27

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -4.12%
Total Return -6.26%
CAGR        -55.70%
MDD         -8.22%
Sharpe      -5.48  (Rf=0, portfolio / full equity curve)
Sharpe      2.29  (Rf=0, trades / position holding periods only)
Trades      77  Win Rate 66% (before fees)
Profit Factor  1.11 (before fees)
SL 14 / TP 0 / sell 63 / final_bar 0
Total Fees  76,306
```
- trades/day ≈ 77/30 ≈ 2.57

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net−; W1 PF1.48 / W2 PF1.22 but net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 전체 2.43/3.27/2.57 <5) |
| C worst net ≥ −2% | FAIL (worst Total Return -6.26%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v34` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: soft div5+RSI<40 below mid→upper/RSI70 제거 → classic bull div(low LL7 + RSI HL7) at/below BB lower; 청산 BB middle only
- next_action: classic LL/HL7 at BB lower → mid only — v34 백테스트.
