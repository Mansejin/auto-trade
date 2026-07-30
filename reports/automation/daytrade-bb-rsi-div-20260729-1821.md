# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 18:21 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v5`
- 가설: BTC daytrade long-only: while close below BB middle, RSI crosses above rsi_signal with RSI<40 (turn in lower half), fade to BB mid or RSI≥55.
- hypers: rsi_cap=40, entry_zone=bb_middle, rsi_exit=55
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return -6.74%
CAGR        -58.47%
MDD         -7.28%
Sharpe      -8.38  (Rf=0, portfolio / full equity curve)
Sharpe      -3.34  (Rf=0, trades / position holding periods only)
Trades      63  Win Rate 63% (before fees)
Profit Factor  0.91 (before fees)
SL 6 / TP 0 / sell 56 / final_bar 1
Total Fees  61,365
```
- trades/day ≈ 63/30 ≈ 2.10 (바 B 미달)

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -11.34%
CAGR        -78.03%
MDD         -11.84%
Sharpe      -9.38  (Rf=0, portfolio / full equity curve)
Sharpe      -11.07  (Rf=0, trades / position holding periods only)
Trades      77  Win Rate 64% (before fees)
Profit Factor  0.76 (before fees)
SL 20 / TP 2 / sell 55 / final_bar 0
Total Fees  72,719
```
- trades/day ≈ 77/30 ≈ 2.57 (바 B 미달)

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -7.41%
CAGR        -62.04%
MDD         -8.95%
Sharpe      -10.24  (Rf=0, portfolio / full equity curve)
Sharpe      -2.95  (Rf=0, trades / position holding periods only)
Trades      70  Win Rate 60% (before fees)
Profit Factor  0.91 (before fees)
SL 6 / TP 0 / sell 64 / final_bar 0
Total Fees  67,395
```
- trades/day ≈ 70/30 ≈ 2.33 (바 B 미달)

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net&lt;0, PF&lt;1.2) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 2.10/2.57/2.33) |
| C worst net ≥ −2% | FAIL (worst Total Return -11.34%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v6` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: mid 페이드 → BB lower reclaim + RSI/signal cross 진입, BB upper/RSI65 라이드 (수수료 출혈 대응)
- next_action: BB lower reclaim + RSI/signal cross 후 BB upper/RSI65 라이드 — v6 백테스트.
