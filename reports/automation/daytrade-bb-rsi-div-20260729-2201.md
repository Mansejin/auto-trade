# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 22:01 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v27`
- 가설: BTC daytrade long-only: BB lower wick (low≤lower, close>lower) with RSI rising 1-bar; exit BB mid or RSI≥60.
- hypers: pattern=lower_wick_rsi_up1, exit=bb_mid_or_rsi60, confirm=close_above_lower
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -12.78%
CAGR        -82.11%
MDD         -15.24%
Sharpe      -11.11  (Rf=0, portfolio / full equity curve)
Sharpe      8.55  (Rf=0, trades / position holding periods only)
Trades      179  Win Rate 72% (before fees)
Profit Factor  1.29 (before fees)
SL 13 / TP 0 / sell 165 / final_bar 1
Total Fees  173,388
```
- trades/day ≈ 179/30 ≈ 5.97

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -26.21%
CAGR        -97.82%
MDD         -26.76%
Sharpe      -14.96  (Rf=0, portfolio / full equity curve)
Sharpe      -10.09  (Rf=0, trades / position holding periods only)
Trades      204  Win Rate 58% (before fees)
Profit Factor  0.75 (before fees)
SL 45 / TP 4 / sell 154 / final_bar 1
Total Fees  170,906
```
- trades/day ≈ 204/30 ≈ 6.80

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return -19.81%
CAGR        -93.78%
MDD         -20.41%
Sharpe      -19.56  (Rf=0, portfolio / full equity curve)
Sharpe      -11.73  (Rf=0, trades / position holding periods only)
Trades      162  Win Rate 60% (before fees)
Profit Factor  0.70 (before fees)
SL 15 / TP 0 / sell 147 / final_bar 0
Total Fees  147,634
```
- trades/day ≈ 162/30 ≈ 5.40

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; nets -12.78/-26.21/-19.81%; W1만 PF 1.29이나 net≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 5.97/6.80/5.40는 빈도만 충족) |
| C worst net ≥ −2% | FAIL (worst Total Return -26.21%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v28` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: lower wick+RSI↑1→mid 제거 → green lower reclaim(low≤lower, close>lower, close>open)+RSI>rsi_signal, 청산 BB upper/RSI65 (수수료 출혈 대응·wider target)
- next_action: green lower reclaim + RSI>signal → upper/RSI65 — v28 백테스트.
