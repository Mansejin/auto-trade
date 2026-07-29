# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 19:01 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v9`
- 가설: BTC daytrade long-only: below BB middle, hidden bull div (price HL + RSI LL lookback 5) with RSI<50, ride to BB upper or RSI≥60.
- hypers: lookback=5, rsi_cap=50, exit=bb_upper_or_rsi60
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 27)
Benchmark   +3.26%
Total Return -1.72%
CAGR        -19.65%
MDD         -2.08%
Sharpe      -5.31  (Rf=0, portfolio / full equity curve)
Sharpe      -18.33  (Rf=0, trades / position holding periods only)
Trades      8  Win Rate 75% (before fees)
Profit Factor  0.42 (before fees)
SL 2 / TP 0 / sell 6 / final_bar 0
Total Fees  7,908
```
- trades/day ≈ 8/30 ≈ 0.27

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -16.19%
Total Return -3.16%
CAGR        -33.21%
MDD         -3.16%
Sharpe      -5.77  (Rf=0, portfolio / full equity curve)
Sharpe      -26.46  (Rf=0, trades / position holding periods only)
Trades      11  Win Rate 45% (before fees)
Profit Factor  0.38 (before fees)
SL 4 / TP 0 / sell 7 / final_bar 0
Total Fees  10,789
```
- trades/day ≈ 11/30 ≈ 0.37

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -4.12%
Total Return -3.95%
CAGR        -39.76%
MDD         -4.30%
Sharpe      -10.80  (Rf=0, portfolio / full equity curve)
Sharpe      -32.78  (Rf=0, trades / position holding periods only)
Trades      11  Win Rate 36% (before fees)
Profit Factor  0.28 (before fees)
SL 5 / TP 0 / sell 6 / final_bar 0
Total Fees  10,890
```
- trades/day ≈ 11/30 ≈ 0.37

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; all Total Return < 0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 0.27/0.37/0.37) |
| C worst net ≥ −2% | FAIL (worst Total Return -3.95%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v10` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: 단일 히든불 제거 → 정규불(BB lower LL/HL) OR 히든불(BB mid HL/LL) lookback4·RSI<48, 청산 BB mid/RSI55
- next_action: 정규+히든불 OR(lookback4) RSI<48 → mid/RSI55 — v10 백테스트.
