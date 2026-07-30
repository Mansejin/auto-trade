# daytrade-bb-rsi-div 런 리포트 — 2026-07-30 00:02 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v39`
- 가설: BTC daytrade long-only: soft bull (low LL4 + RSI HL4) with low≤BB lower and green close; exit BB upper or RSI≥55.
- hypers: pattern=soft_ll_hl4_green_at_lower, exit=bb_upper_or_rsi55, div_lookback=4
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 26)
Benchmark   +3.26%
Total Return -4.20%
CAGR        -41.76%
MDD         -5.66%
Sharpe      -4.79  (Rf=0, portfolio / full equity curve)
Sharpe      7.56  (Rf=0, trades / position holding periods only)
Trades      62  Win Rate 66% (before fees)
Profit Factor  1.28 (before fees)
SL 7 / TP 0 / sell 55 / final_bar 0
Total Fees  61,242
```
- trades/day ≈ 62/30 ≈ 2.07

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -16.19%
Total Return -8.15%
CAGR        -65.69%
MDD         -9.81%
Sharpe      -5.31  (Rf=0, portfolio / full equity curve)
Sharpe      -0.06  (Rf=0, trades / position holding periods only)
Trades      83  Win Rate 61% (before fees)
Profit Factor  0.98 (before fees)
SL 24 / TP 0 / sell 58 / final_bar 1
Total Fees  77,917
```
- trades/day ≈ 83/30 ≈ 2.77

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -4.12%
Total Return -7.12%
CAGR        -60.55%
MDD         -7.90%
Sharpe      -8.27  (Rf=0, portfolio / full equity curve)
Sharpe      -0.42  (Rf=0, trades / position holding periods only)
Trades      72  Win Rate 69% (before fees)
Profit Factor  0.99 (before fees)
SL 10 / TP 0 / sell 62 / final_bar 0
Total Fees  70,654
```
- trades/day ≈ 72/30 ≈ 2.40

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전 윈도우 net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 2.07/2.77/2.40 ≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -8.15%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v40` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: soft classic LL/HL4+green@lower→upper/RSI55 제거 → hidden bull HL/LL2 @lower; 청산 BB mid or RSI≥55
- next_action: hidden HL/LL2 @lower → mid/RSI55 — v40 백테스트.
