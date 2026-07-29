# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 23:11 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v34`
- 가설: BTC daytrade long-only: classic bull div (low LL7 + RSI HL7) at/below BB lower; exit BB middle only.
- hypers: pattern=classic_ll_hl7_at_bb_lower, exit=bb_middle_only, div_lookback=7
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 29)
Benchmark   +3.26%
Total Return -0.70%
CAGR        -8.43%
MDD         -0.99%
Sharpe      -3.26  (Rf=0, portfolio / full equity curve)
Sharpe      -8.95  (Rf=0, trades / position holding periods only)
Trades      5  Win Rate 60% (before fees)
Profit Factor  0.76 (before fees)
SL 1 / TP 0 / sell 4 / final_bar 0
Total Fees  4,968
```
- trades/day ≈ 5/30 ≈ 0.17

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 29)
Benchmark   -16.19%
Total Return -0.10%
CAGR        -1.30%
MDD         -0.77%
Sharpe      -0.57  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 0 / TP 0 / sell 1 / final_bar 0
Total Fees  999
```
- trades/day ≈ 1/30 ≈ 0.03

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 29)
Benchmark   -4.12%
Total Return -0.84%
CAGR        -10.03%
MDD         -0.95%
Sharpe      -4.75  (Rf=0, portfolio / full equity curve)
Sharpe      -47.89  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 50% (before fees)
Profit Factor  0.20 (before fees)
SL 1 / TP 0 / sell 1 / final_bar 0
Total Fees  1,996
```
- trades/day ≈ 2/30 ≈ 0.07

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net−; PF 0.76/0.00/0.20) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 전체 0.17/0.03/0.07 <5) |
| C worst net ≥ −2% | PASS (worst Total Return -0.84%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v35` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: classic LL/HL7→mid only 제거 → hidden bull div(price HL3 + RSI LL3) at/below BB lower; 청산 BB upper or RSI≥65
- next_action: hidden bull HL3+RSI LL3 at BB lower → upper/RSI65 — v35 백테스트.
