# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 23:31 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v36`
- 가설: BTC daytrade long-only: soft classic bull (close LL2 + RSI HL2) below BB mid with RSI<50; exit BB upper or RSI≥60.
- hypers: pattern=soft_ll_hl2_below_mid_rsi50, exit=bb_upper_or_rsi60, div_lookback=2
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 24)
Benchmark   +3.26%
Total Return -3.25%
CAGR        -34.02%
MDD         -5.94%
Sharpe      -2.18  (Rf=0, portfolio / full equity curve)
Sharpe      10.25  (Rf=0, trades / position holding periods only)
Trades      106  Win Rate 72% (before fees)
Profit Factor  1.45 (before fees)
SL 19 / TP 0 / sell 86 / final_bar 1
Total Fees  105,688
```
- trades/day ≈ 106/30 ≈ 3.53

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -16.19%
Total Return -14.76%
CAGR        -86.60%
MDD         -14.93%
Sharpe      -7.87  (Rf=0, portfolio / full equity curve)
Sharpe      -3.86  (Rf=0, trades / position holding periods only)
Trades      113  Win Rate 57% (before fees)
Profit Factor  0.86 (before fees)
SL 41 / TP 2 / sell 69 / final_bar 1
Total Fees  102,759
```
- trades/day ≈ 113/30 ≈ 3.77

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -4.12%
Total Return -12.03%
CAGR        -80.08%
MDD         -13.18%
Sharpe      -9.99  (Rf=0, portfolio / full equity curve)
Sharpe      -4.18  (Rf=0, trades / position holding periods only)
Trades      100  Win Rate 67% (before fees)
Profit Factor  0.84 (before fees)
SL 17 / TP 0 / sell 82 / final_bar 1
Total Fees  95,736
```
- trades/day ≈ 100/30 ≈ 3.33

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전 윈도우 net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 모두 <5) |
| C worst net ≥ −2% | FAIL (worst Total Return -14.76%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v37` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: soft LL/HL2 below mid 제거 → RSI bull cross(signal) at BB lower + RSI<45; 청산 BB upper or RSI≥65
- next_action: RSI signal cross at BB lower RSI<45 → upper/RSI65 — v37 백테스트.
