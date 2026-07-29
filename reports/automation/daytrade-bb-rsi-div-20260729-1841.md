# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 18:41 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v7`
- 가설: BTC daytrade long-only: while close < BB middle, RSI cross_above rsi_signal (no OS cap), ride to BB upper or RSI≥70.
- hypers: entry=below_mid+rsi_signal_cross, exit_band=bb_upper, rsi_exit=70
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return -7.77%
CAGR        -63.85%
MDD         -10.21%
Sharpe      -4.46  (Rf=0, portfolio / full equity curve)
Sharpe      6.65  (Rf=0, trades / position holding periods only)
Trades      152  Win Rate 69% (before fees)
Profit Factor  1.30 (before fees)
SL 25 / TP 0 / sell 126 / final_bar 1
Total Fees  147,530
```
- trades/day ≈ 152/30 ≈ 5.07

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -28.17%
CAGR        -98.45%
MDD         -29.04%
Sharpe      -12.25  (Rf=0, portfolio / full equity curve)
Sharpe      -7.27  (Rf=0, trades / position holding periods only)
Trades      183  Win Rate 51% (before fees)
Profit Factor  0.74 (before fees)
SL 75 / TP 2 / sell 105 / final_bar 1
Total Fees  148,658
```
- trades/day ≈ 183/30 ≈ 6.10

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -11.33%
CAGR        -77.99%
MDD         -13.55%
Sharpe      -7.88  (Rf=0, portfolio / full equity curve)
Sharpe      1.63  (Rf=0, trades / position holding periods only)
Trades      134  Win Rate 67% (before fees)
Profit Factor  1.09 (before fees)
SL 21 / TP 0 / sell 112 / final_bar 1
Total Fees  130,130
```
- trades/day ≈ 134/30 ≈ 4.47 (바 B 미달)

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; all Total Return < 0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 5.07/6.10/4.47) |
| C worst net ≥ −2% | FAIL (worst Total Return -28.17%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v8` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: RSI/signal ride 제거 → BB lower에서 price LL + RSI HL(lookback 3)·RSI<45, 청산 BB mid/RSI55 페이드
- next_action: BB lower + price LL/RSI HL(lookback3) RSI<45 → mid/RSI55 페이드 — v8 백테스트.
