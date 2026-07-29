# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 18:51 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v8`
- 가설: BTC daytrade long-only: at BB lower, price LL + RSI HL (lookback 3) with RSI<45, fade to BB middle or RSI≥55.
- hypers: lookback=3, rsi_cap=45, exit=bb_mid_or_rsi55
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 25)
Benchmark   +3.26%
Total Return -0.58%
CAGR        -7.08%
MDD         -1.17%
Sharpe      -2.60  (Rf=0, portfolio / full equity curve)
Sharpe      22.03  (Rf=0, trades / position holding periods only)
Trades      10  Win Rate 60% (before fees)
Profit Factor  1.74 (before fees)
SL 0 / TP 0 / sell 10 / final_bar 0
Total Fees  9,940
```
- trades/day ≈ 10/30 ≈ 0.33

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -16.19%
Total Return -4.85%
CAGR        -46.49%
MDD         -5.08%
Sharpe      -10.04  (Rf=0, portfolio / full equity curve)
Sharpe      -71.09  (Rf=0, trades / position holding periods only)
Trades      11  Win Rate 45% (before fees)
Profit Factor  0.20 (before fees)
SL 6 / TP 0 / sell 5 / final_bar 0
Total Fees  10,754
```
- trades/day ≈ 11/30 ≈ 0.37

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -4.12%
Total Return -3.31%
CAGR        -34.56%
MDD         -3.83%
Sharpe      -8.32  (Rf=0, portfolio / full equity curve)
Sharpe      -35.35  (Rf=0, trades / position holding periods only)
Trades      12  Win Rate 50% (before fees)
Profit Factor  0.33 (before fees)
SL 3 / TP 0 / sell 9 / final_bar 0
Total Fees  11,869
```
- trades/day ≈ 12/30 ≈ 0.40

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; all Total Return < 0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 0.33/0.37/0.40) |
| C worst net ≥ −2% | FAIL (worst Total Return -4.85%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v9` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: 정규 bull div(LL/HL) 페이드 제거 → BB mid 이하에서 히든 불(price HL + RSI LL lookback5)·RSI<50, 청산 BB upper/RSI60
- next_action: BB mid 이하 + price HL/RSI LL(lookback5) RSI<50 → upper/RSI60 히든불 — v9 백테스트.
