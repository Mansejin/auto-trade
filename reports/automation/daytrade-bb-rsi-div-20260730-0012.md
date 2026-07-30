# daytrade-bb-rsi-div 런 리포트 — 2026-07-30 00:12 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v40`
- 가설: BTC daytrade long-only: hidden bull (low HL2 + RSI LL2) at/below BB lower; exit BB mid or RSI≥55.
- hypers: pattern=hidden_hl_ll2_at_lower, exit=bb_mid_or_rsi55, div_lookback=2
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 24)
Benchmark   +3.26%
Total Return -0.38%
CAGR        -4.73%
MDD         -0.90%
Sharpe      -0.95  (Rf=0, portfolio / full equity curve)
Sharpe      58.39  (Rf=0, trades / position holding periods only)
Trades      23  Win Rate 74% (before fees)
Profit Factor  5.06 (before fees)
SL 0 / TP 0 / sell 23 / final_bar 0
Total Fees  22,939
```
- trades/day ≈ 23/30 ≈ 0.77

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -16.19%
Total Return -1.60%
CAGR        -18.40%
MDD         -3.09%
Sharpe      -2.41  (Rf=0, portfolio / full equity curve)
Sharpe      2.61  (Rf=0, trades / position holding periods only)
Trades      18  Win Rate 67% (before fees)
Profit Factor  1.07 (before fees)
SL 3 / TP 0 / sell 15 / final_bar 0
Total Fees  17,962
```
- trades/day ≈ 18/30 ≈ 0.60

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 24)
Benchmark   -4.12%
Total Return -1.75%
CAGR        -19.93%
MDD         -2.44%
Sharpe      -4.14  (Rf=0, portfolio / full equity curve)
Sharpe      3.62  (Rf=0, trades / position holding periods only)
Trades      20  Win Rate 65% (before fees)
Profit Factor  1.11 (before fees)
SL 2 / TP 0 / sell 18 / final_bar 0
Total Fees  19,826
```
- trades/day ≈ 20/30 ≈ 0.67

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전 윈도우 net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 0.77/0.60/0.67 ≪5) |
| C worst net ≥ −2% | PASS (worst Total Return -1.75%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v41` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: hidden HL/LL2@lower→mid/RSI55 제거 → close reclaim BB lower + soft bull(close LL3 + RSI HL3); 청산 BB middle only
- next_action: BB lower reclaim + soft LL/HL3 → mid only — v41 백테스트.
