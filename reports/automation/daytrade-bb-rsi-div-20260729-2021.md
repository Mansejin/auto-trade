# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 20:21 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v17`
- 가설: BTC daytrade long-only: prior low tags BB lower then same-bar close snaps above BB mid with RSI>rsi_signal; exit BB upper or RSI≥70.
- hypers: pattern=lower_snap_through_mid, rsi_vs_signal=gt, exit=bb_upper_or_rsi70
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return -3.41%
CAGR        -35.42%
MDD         -4.94%
Sharpe      -6.53  (Rf=0, portfolio / full equity curve)
Sharpe      -3.12  (Rf=0, trades / position holding periods only)
Trades      30  Win Rate 70% (before fees)
Profit Factor  0.92 (before fees)
SL 6 / TP 0 / sell 24 / final_bar 0
Total Fees  29,790
```
- trades/day ≈ 30/30 ≈ 1.00

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -4.88%
CAGR        -46.70%
MDD         -6.38%
Sharpe      -6.12  (Rf=0, portfolio / full equity curve)
Sharpe      -12.35  (Rf=0, trades / position holding periods only)
Trades      28  Win Rate 61% (before fees)
Profit Factor  0.69 (before fees)
SL 9 / TP 0 / sell 19 / final_bar 0
Total Fees  26,876
```
- trades/day ≈ 28/30 ≈ 0.93

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -1.72%
CAGR        -19.63%
MDD         -3.53%
Sharpe      -2.66  (Rf=0, portfolio / full equity curve)
Sharpe      14.53  (Rf=0, trades / position holding periods only)
Trades      38  Win Rate 71% (before fees)
Profit Factor  1.71 (before fees)
SL 2 / TP 0 / sell 36 / final_bar 0
Total Fees  37,843
```
- trades/day ≈ 38/30 ≈ 1.27

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; all Total Return ≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 1.00/0.93/1.27≪5) |
| C worst net ≥ −2% | FAIL (worst Total Return -4.88%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v18` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: lower snap-through mid 제거 → close<BB mid 상태에서 RSI 50 상향 돌파(prior≤50) + mid/RSI60 단기 페이드 (v7 signal-cross·upper ride와 구조 다름)
- next_action: close<mid + RSI≤50→>50 flip → mid/RSI60 페이드 — v18 백테스트.
