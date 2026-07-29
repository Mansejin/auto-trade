# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 22:32 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v30`
- 가설: BTC daytrade long-only: RSI≤30→>30 reclaim at/below BB lower with soft bull div lookback4; exit BB mid or RSI≥55.
- hypers: pattern=rsi30_reclaim_at_lower_softdiv4, exit=bb_mid_or_rsi55, div_lookback=4
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 26)
Benchmark   +3.26%
Total Return +0.00%
CAGR        +0.00%
MDD         0.00%
Sharpe      0.00  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      0  Win Rate N/A (0 executed trades) (before fees)
Profit Factor  N/A (0 executed trades) (before fees)
SL 0 / TP 0 / sell 0 / final_bar 0
Total Fees  0
```
- trades/day ≈ 0/30 ≈ 0.00

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -16.19%
Total Return +0.00%
CAGR        +0.00%
MDD         0.00%
Sharpe      0.00  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      0  Win Rate N/A (0 executed trades) (before fees)
Profit Factor  N/A (0 executed trades) (before fees)
SL 0 / TP 0 / sell 0 / final_bar 0
Total Fees  0
```
- trades/day ≈ 0/30 ≈ 0.00

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -4.12%
Total Return +0.00%
CAGR        +0.00%
MDD         0.00%
Sharpe      0.00  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      0  Win Rate N/A (0 executed trades) (before fees)
Profit Factor  N/A (0 executed trades) (before fees)
SL 0 / TP 0 / sell 0 / final_bar 0
Total Fees  0
```
- trades/day ≈ 0/30 ≈ 0.00

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; nets +0.00% all; PF N/A; net>0 없음) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 0.00/0.00/0.00) |
| C worst net ≥ −2% | PASS (worst Total Return +0.00%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v31` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: RSI30 단일봉 reclaim+softdiv4 at lower→mid 제거 → RSI≤30 이후 2바 상승(failure-swing) + BB lower wick green + RSI>rsi_signal; 청산 BB upper or RSI≥65
- next_action: RSI failure-swing(≤30→2바상승) + lower wick green + RSI>signal → upper/RSI65 — v31 백테스트.
