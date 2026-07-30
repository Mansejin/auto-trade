# daytrade-bb-rsi-div 런 리포트 — 2026-07-30 00:41 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v43`
- 가설: BTC daytrade long-only: wick reject at BB lower (low≤lower∧close>lower) with RSI<35; exit BB mid or RSI≥50.
- hypers: pattern=wick_reject_lower_rsi35, exit=bb_mid_or_rsi50, rsi_cap=35
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return -5.67%
CAGR        -52.03%
MDD         -6.20%
Sharpe      -6.85  (Rf=0, portfolio / full equity curve)
Sharpe      -0.98  (Rf=0, trades / position holding periods only)
Trades      56  Win Rate 70% (before fees)
Profit Factor  0.98 (before fees)
SL 6 / TP 0 / sell 49 / final_bar 1
Total Fees  55,103
```
- trades/day ≈ 56/30 ≈ 1.87

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -12.41%
CAGR        -81.13%
MDD         -13.30%
Sharpe      -8.49  (Rf=0, portfolio / full equity curve)
Sharpe      -10.41  (Rf=0, trades / position holding periods only)
Trades      79  Win Rate 52% (before fees)
Profit Factor  0.77 (before fees)
SL 25 / TP 0 / sell 54 / final_bar 0
Total Fees  73,984
```
- trades/day ≈ 79/30 ≈ 2.63

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -9.29%
CAGR        -70.70%
MDD         -10.97%
Sharpe      -11.42  (Rf=0, portfolio / full equity curve)
Sharpe      -12.76  (Rf=0, trades / position holding periods only)
Trades      63  Win Rate 62% (before fees)
Profit Factor  0.68 (before fees)
SL 9 / TP 0 / sell 53 / final_bar 1
Total Fees  61,160
```
- trades/day ≈ 63/30 ≈ 2.10

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전 윈도우 net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 최대≈2.63 ≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -12.41%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v44` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: wick reject+RSI35→mid/RSI50 제거 → close≤BB lower + RSI rising(rsi>rsi[1]) + RSI<40; 청산 BB upper or RSI≥65 (mid 청산 수수료 출혈 회피)
- next_action: close≤lower + RSI rising + RSI<40 → upper/RSI65 — v44 백테스트.
