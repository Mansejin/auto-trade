# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 22:21 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v29`
- 가설: BTC daytrade long-only: RSI signal bull cross below BB mid with soft bull div lookback6; exit BB upper only.
- hypers: pattern=rsi_signal_cross_softdiv6_below_mid, exit=bb_upper_only, div_lookback=6
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 28)
Benchmark   +3.26%
Total Return -0.39%
CAGR        -4.80%
MDD         -4.54%
Sharpe      -0.22  (Rf=0, portfolio / full equity curve)
Sharpe      13.81  (Rf=0, trades / position holding periods only)
Trades      77  Win Rate 74% (before fees)
Profit Factor  1.74 (before fees)
SL 10 / TP 0 / sell 66 / final_bar 1
Total Fees  76,875
```
- trades/day ≈ 77/30 ≈ 2.57

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 28)
Benchmark   -16.19%
Total Return -10.68%
CAGR        -75.88%
MDD         -13.20%
Sharpe      -6.00  (Rf=0, portfolio / full equity curve)
Sharpe      -1.57  (Rf=0, trades / position holding periods only)
Trades      95  Win Rate 57% (before fees)
Profit Factor  0.92 (before fees)
SL 35 / TP 2 / sell 57 / final_bar 1
Total Fees  86,734
```
- trades/day ≈ 95/30 ≈ 3.17

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 28)
Benchmark   -4.12%
Total Return -6.07%
CAGR        -54.51%
MDD         -8.62%
Sharpe      -5.34  (Rf=0, portfolio / full equity curve)
Sharpe      4.30  (Rf=0, trades / position holding periods only)
Trades      88  Win Rate 69% (before fees)
Profit Factor  1.20 (before fees)
SL 15 / TP 0 / sell 73 / final_bar 0
Total Fees  87,171
```
- trades/day ≈ 88/30 ≈ 2.93

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; nets -0.39/-10.68/-6.07%; W1 PF 1.74·W3 PF 1.20이나 모두 net≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 2.57/3.17/2.93) |
| C worst net ≥ −2% | FAIL (worst Total Return -10.68%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v30` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: RSI signal cross+soft div6 below mid→upper 제거 → RSI≤30→>30 reclaim at/below BB lower + soft bull div lookback4; 청산 BB mid or RSI≥55
- next_action: RSI30 reclaim at lower + soft div4 → mid/RSI55 — v30 백테스트.
