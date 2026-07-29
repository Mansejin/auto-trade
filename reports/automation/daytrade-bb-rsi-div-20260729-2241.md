# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 22:41 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v31`
- 가설: BTC daytrade long-only: RSI≤30 then 2-bar rise (failure-swing) + BB lower wick green candle + RSI>rsi_signal; exit BB upper or RSI≥65.
- hypers: pattern=rsi_failure_swing_lower_wick_green_gt_signal, exit=bb_upper_or_rsi65, div_lookback=2
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 24)
Benchmark   +3.26%
Total Return -0.44%
CAGR        -5.38%
MDD         -1.78%
Sharpe      -1.15  (Rf=0, portfolio / full equity curve)
Sharpe      3.63  (Rf=0, trades / position holding periods only)
Trades      7  Win Rate 71% (before fees)
Profit Factor  1.16 (before fees)
SL 2 / TP 0 / sell 5 / final_bar 0
Total Fees  6,952
```
- trades/day ≈ 7/30 ≈ 0.23

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -16.19%
Total Return -0.30%
CAGR        -3.72%
MDD         -1.07%
Sharpe      -0.96  (Rf=0, portfolio / full equity curve)
Sharpe      2.16  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 25% (before fees)
Profit Factor  1.10 (before fees)
SL 1 / TP 0 / sell 3 / final_bar 0
Total Fees  4,009
```
- trades/day ≈ 4/30 ≈ 0.13

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -4.12%
Total Return +0.36%
CAGR        +4.61%
MDD         -0.37%
Sharpe      1.63  (Rf=0, portfolio / full equity curve)
Sharpe      128.01  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 100% (before fees)
Profit Factor  ∞ (before fees)
SL 0 / TP 0 / sell 2 / final_bar 0
Total Fees  2,003
```
- trades/day ≈ 2/30 ≈ 0.07

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (1/3; W3만 net+0.36%·PF∞; W1 PF1.16<1.2 & net−; W2 net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 W3만 0.07≪5; 전체 0.23/0.13/0.07) |
| C worst net ≥ −2% | PASS (worst Total Return -0.44%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v32` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: RSI failure-swing+lower wick green+RSI>signal 제거 → close cross_above BB lower + RSI↑1 + RSI<50; 청산 BB upper or RSI≥70
- next_action: BB lower reclaim cross + RSI↑1 RSI<50 → upper/RSI70 — v32 백테스트.
