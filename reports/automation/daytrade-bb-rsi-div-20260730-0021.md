# daytrade-bb-rsi-div 런 리포트 — 2026-07-30 00:21 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v41`
- 가설: BTC daytrade long-only: close reclaim BB lower (cross_above) with soft bull (close LL3 + RSI HL3); exit BB middle only.
- hypers: pattern=reclaim_soft_ll_hl3, exit=bb_mid_only, div_lookback=3
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 25)
Benchmark   +3.26%
Total Return -6.52%
CAGR        -57.20%
MDD         -7.23%
Sharpe      -9.43  (Rf=0, portfolio / full equity curve)
Sharpe      -13.08  (Rf=0, trades / position holding periods only)
Trades      46  Win Rate 65% (before fees)
Profit Factor  0.70 (before fees)
SL 6 / TP 0 / sell 39 / final_bar 1
Total Fees  45,140
```
- trades/day ≈ 46/30 ≈ 1.53

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -16.19%
Total Return -4.09%
CAGR        -40.89%
MDD         -5.48%
Sharpe      -3.44  (Rf=0, portfolio / full equity curve)
Sharpe      6.04  (Rf=0, trades / position holding periods only)
Trades      58  Win Rate 67% (before fees)
Profit Factor  1.17 (before fees)
SL 9 / TP 0 / sell 49 / final_bar 0
Total Fees  56,912
```
- trades/day ≈ 58/30 ≈ 1.93

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -4.12%
Total Return -7.11%
CAGR        -60.47%
MDD         -7.68%
Sharpe      -10.07  (Rf=0, portfolio / full equity curve)
Sharpe      -13.27  (Rf=0, trades / position holding periods only)
Trades      48  Win Rate 58% (before fees)
Profit Factor  0.64 (before fees)
SL 6 / TP 0 / sell 42 / final_bar 0
Total Fees  46,535
```
- trades/day ≈ 48/30 ≈ 1.60

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전 윈도우 net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 1.53/1.93/1.60 ≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -7.11%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v42` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: reclaim+soft LL/HL3→mid 제거 → RSI leave-OS (prior<30∧current≥30) while close≤BB lower; 청산 BB mid or RSI≥50
- next_action: RSI leave-OS30 @BB lower → mid/RSI50 — v42 백테스트.
