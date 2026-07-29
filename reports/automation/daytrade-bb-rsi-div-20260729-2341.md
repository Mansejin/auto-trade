# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 23:41 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v37`
- 가설: BTC daytrade long-only: RSI bull cross above signal at/below BB lower with RSI<45; exit BB upper or RSI≥65.
- hypers: pattern=rsi_signal_cross_at_bb_lower_rsi45, exit=bb_upper_or_rsi65, band=bb_lower_touch
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -1.59%
CAGR        -18.23%
MDD         -4.92%
Sharpe      -1.69  (Rf=0, portfolio / full equity curve)
Sharpe      7.65  (Rf=0, trades / position holding periods only)
Trades      39  Win Rate 72% (before fees)
Profit Factor  1.37 (before fees)
SL 7 / TP 0 / sell 32 / final_bar 0
Total Fees  38,477
```
- trades/day ≈ 39/30 ≈ 1.30

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -5.96%
CAGR        -53.85%
MDD         -8.25%
Sharpe      -4.45  (Rf=0, portfolio / full equity curve)
Sharpe      -1.67  (Rf=0, trades / position holding periods only)
Trades      51  Win Rate 51% (before fees)
Profit Factor  0.93 (before fees)
SL 21 / TP 1 / sell 29 / final_bar 0
Total Fees  48,314
```
- trades/day ≈ 51/30 ≈ 1.70

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return -3.12%
CAGR        -32.90%
MDD         -4.42%
Sharpe      -3.93  (Rf=0, portfolio / full equity curve)
Sharpe      3.05  (Rf=0, trades / position holding periods only)
Trades      41  Win Rate 76% (before fees)
Profit Factor  1.13 (before fees)
SL 9 / TP 0 / sell 32 / final_bar 0
Total Fees  40,841
```
- trades/day ≈ 41/30 ≈ 1.37

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전 윈도우 net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 모두 <5) |
| C worst net ≥ −2% | FAIL (worst Total Return -5.96%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v38` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: RSI×signal cross@lower 제거 → classic bull LL/HL5 + RSI>signal at/below BB lower; 청산 BB middle only (수수료·보유구간 축소)
- next_action: classic LL/HL5 + RSI>signal @lower → mid only — v38 백테스트.
