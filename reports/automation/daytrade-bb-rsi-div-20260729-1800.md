# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 18:00 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v2`
- 가설: BTC daytrade long-only: BB lower reclaim with RSI still below mid and RSI rising vs lookback (bullish momentum vs band stress), fade to BB mid.
- hypers: rsi_cap=50, bb_std=2.0, div_lookback=3
- fee: 툴킷 기본(수수료 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 25)
Benchmark   +3.26%
Total Return -8.32%
CAGR        -66.48%
MDD         -9.08%
Sharpe      -10.57  (Rf=0, portfolio / full equity curve)
Sharpe      -9.66  (Rf=0, trades / position holding periods only)
Trades      66  Win Rate 64% (before fees)
Profit Factor  0.77 (before fees)
SL 7 / TP 0 / sell 58 / final_bar 1
Total Fees  64,201
```
- trades/day ≈ 66/30 ≈ 2.20 (바 B 미달)

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -16.19%
Total Return -10.37%
CAGR        -74.78%
MDD         -12.37%
Sharpe      -8.17  (Rf=0, portfolio / full equity curve)
Sharpe      -3.65  (Rf=0, trades / position holding periods only)
Trades      92  Win Rate 64% (before fees)
Profit Factor  0.89 (before fees)
SL 19 / TP 2 / sell 71 / final_bar 0
Total Fees  85,145
```
- trades/day ≈ 92/30 ≈ 3.07 (바 B 미달)

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -4.12%
Total Return -9.35%
CAGR        -70.95%
MDD         -10.52%
Sharpe      -11.21  (Rf=0, portfolio / full equity curve)
Sharpe      -7.38  (Rf=0, trades / position holding periods only)
Trades      77  Win Rate 62% (before fees)
Profit Factor  0.80 (before fees)
SL 9 / TP 0 / sell 68 / final_bar 0
Total Fees  73,659
```
- trades/day ≈ 77/30 ≈ 2.57 (바 B 미달)

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3, 전부 net≤0, PF 0.77/0.89/0.80) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 최대 ≈3.07) |
| C worst net ≥ −2% | FAIL (worst Total Return -10.37%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v3`
- next_action: BB lower 터치에서 RSI 35 재탈환(직전봉 <35) 후 BB mid로 페이드.
