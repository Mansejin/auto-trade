# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 17:52 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v1`
- 가설: BTC daytrade: RSI extreme + BB outer band, divergence confirms fade to mid; SL beyond signal extreme.
- hypers: rsi_os=30, bb_std=2.0, div_lookback=5
- fee: 툴킷 기본(수수료 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 27)
Benchmark   +3.26%
Total Return -0.42%
CAGR        -5.16%
MDD         -0.65%
Sharpe      -2.05  (Rf=0, portfolio / full equity curve)
Sharpe      -58.99  (Rf=0, trades / position holding periods only)
Trades      2  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 0 / TP 0 / sell 2 / final_bar 0
Total Fees  1,997
```
- trades/day ≈ 2/30 ≈ 0.07 (바 B 미달)

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -16.19%
Total Return -0.90%
CAGR        -10.75%
MDD         -0.99%
Sharpe      -5.34  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 1 / TP 0 / sell 0 / final_bar 0
Total Fees  995
```
- trades/day ≈ 1/30 ≈ 0.03 (바 B 미달)

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 27)
Benchmark   -4.12%
Total Return -2.95%
CAGR        -31.37%
MDD         -2.95%
Sharpe      -10.81  (Rf=0, portfolio / full equity curve)
Sharpe      -161.43  (Rf=0, trades / position holding periods only)
Trades      4  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 3 / TP 0 / sell 1 / final_bar 0
Total Fees  3,938
```
- trades/day ≈ 4/30 ≈ 0.13 (바 B 미달)

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3, 전부 net≤0, PF 0.00) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 최대 ~0.13) |
| C worst net ≥ −2% | FAIL (worst Total Return -2.95%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v2`
- next_action: BB lower reclaim + RSI below mid + RSI rising vs lookback으로 페이드(하드 OS/가격 LL 제거).
