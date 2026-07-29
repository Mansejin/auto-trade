# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 18:07 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v3`
- 가설: BTC daytrade long-only: while close at/below BB lower, RSI reclaim above 35 (prior bar < 35), fade to BB mid or RSI≥55.
- hypers: rsi_reclaim=35, bb_std=2.0, rsi_exit=55
- fee: 툴킷 기본(수수료 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -0.26%
CAGR        -3.16%
MDD         -1.12%
Sharpe      -1.15  (Rf=0, portfolio / full equity curve)
Sharpe      6.60  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 50% (before fees)
Profit Factor  1.17 (before fees)
SL 1 / TP 0 / sell 3 / final_bar 0
Total Fees  4,020
```
- trades/day ≈ 4/30 ≈ 0.13 (바 B 미달)

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -1.82%
CAGR        -20.59%
MDD         -2.02%
Sharpe      -6.53  (Rf=0, portfolio / full equity curve)
Sharpe      -58.36  (Rf=0, trades / position holding periods only)
Trades      5  Win Rate 20% (before fees)
Profit Factor  0.07 (before fees)
SL 1 / TP 0 / sell 4 / final_bar 0
Total Fees  4,944
```
- trades/day ≈ 5/30 ≈ 0.17 (바 B 미달)

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return +0.04%
CAGR        +0.52%
MDD         -0.25%
Sharpe      0.45  (Rf=0, portfolio / full equity curve)
Sharpe      55.84  (Rf=0, trades / position holding periods only)
Trades      3  Win Rate 67% (before fees)
Profit Factor  49.84 (before fees)
SL 0 / TP 0 / sell 3 / final_bar 0
Total Fees  3,000
```
- trades/day ≈ 3/30 ≈ 0.10 (바 B 미달)

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (1/3: W3만 통과; W1 net≤0·PF1.17, W2 net≤0·PF0.07) |
| B 통과 윈도우 trades/day≥5 | FAIL (W3 ≈0.10) |
| C worst net ≥ −2% | PASS (worst Total Return -1.82%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v4` (JSON 저장·validate OK, 백테스트는 다음 런)
- next_action: BB lower에서 RSI가 rsi_signal을 cross_above(RSI<45)한 뒤 BB mid/RSI60으로 페이드 — v4 백테스트.
