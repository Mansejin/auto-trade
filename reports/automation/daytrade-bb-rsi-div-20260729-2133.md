# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 21:33 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v24`
- 가설: BTC daytrade long-only: under BB mid, 1-bar soft bull divergence (close < close[1] while RSI > RSI[1]); quick fade to BB mid or RSI≥50.
- hypers: pattern=1bar_soft_div_under_mid, div_lookback=1, exit=bb_mid_or_rsi50
- fee: 툴킷 기본(수수료 출력 있음; 체결 0이라 Total Fees 0)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
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
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
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
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
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
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 0 trades, Total Return +0.00%는 net>0 아님) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 0.00/0.00/0.00≪5) |
| C worst net ≥ −2% | PASS (worst Total Return +0.00%) |
| D fee on | PASS (Total Fees 출력; 체결 0) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v25` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: under-mid 1-bar soft div 제거 → BB lower reclaim + RSI≤40 + soft div lookback3, 청산 BB mid/RSI55
- next_action: lower reclaim + RSI≤40 + soft div3 → mid/RSI55 — v25 백테스트.
