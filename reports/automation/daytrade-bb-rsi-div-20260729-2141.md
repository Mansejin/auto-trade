# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 21:41 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v25`
- 가설: BTC daytrade long-only: BB lower reclaim (prior close ≤ lower, close > lower) with RSI≤40 and soft bull div lookback3 (close < close[3] & RSI > RSI[3]); exit BB mid or RSI≥55.
- hypers: pattern=lower_reclaim_rsi40_softdiv3, div_lookback=3, exit=bb_mid_or_rsi55
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 25)
Benchmark   +3.26%
Total Return -5.19%
CAGR        -48.87%
MDD         -5.60%
Sharpe      -8.50  (Rf=0, portfolio / full equity curve)
Sharpe      -19.88  (Rf=0, trades / position holding periods only)
Trades      30  Win Rate 60% (before fees)
Profit Factor  0.55 (before fees)
SL 5 / TP 0 / sell 24 / final_bar 1
Total Fees  29,503
```
- trades/day ≈ 30/30 ≈ 1.00

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -16.19%
Total Return -1.40%
CAGR        -16.31%
MDD         -3.48%
Sharpe      -1.25  (Rf=0, portfolio / full equity curve)
Sharpe      12.34  (Rf=0, trades / position holding periods only)
Trades      44  Win Rate 66% (before fees)
Profit Factor  1.39 (before fees)
SL 7 / TP 2 / sell 35 / final_bar 0
Total Fees  43,298
```
- trades/day ≈ 44/30 ≈ 1.47

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -4.12%
Total Return -6.28%
CAGR        -55.82%
MDD         -6.79%
Sharpe      -9.63  (Rf=0, portfolio / full equity curve)
Sharpe      -16.95  (Rf=0, trades / position holding periods only)
Trades      37  Win Rate 57% (before fees)
Profit Factor  0.55 (before fees)
SL 6 / TP 0 / sell 31 / final_bar 0
Total Fees  35,882
```
- trades/day ≈ 37/30 ≈ 1.23

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; nets -5.19/-1.40/-6.28%; W2만 PF 1.39이나 net≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 1.00/1.47/1.23≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -6.28%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v26` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: lower reclaim+RSI40+softdiv3 제거 → lower touch + RSI>rsi_signal + RSI<45, 청산 BB upper/RSI70
- next_action: lower touch + RSI>signal RSI<45 → upper/RSI70 — v26 백테스트.
