# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 21:51 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v26`
- 가설: BTC daytrade long-only: close ≤ BB lower with RSI > RSI signal and RSI < 45 (momentum turn at lower band); exit BB upper or RSI≥70.
- hypers: pattern=lower_touch_rsi_gt_signal, rsi_cap=45, exit=bb_upper_or_rsi70
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 22)
Benchmark   +3.26%
Total Return +0.00%
CAGR        +0.00%
MDD         0.00%
Sharpe      0.00  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      0  Win Rate N/A (0 executed trades) (before fees)
Profit Factor  N/A (0 executed trades) (before fees)
SL 0 / TP 0 / sell 0 / final_bar 0
Total Fees  0
```
- trades/day ≈ 0/30 ≈ 0.00

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -16.19%
Total Return -0.90%
CAGR        -10.74%
MDD         -1.06%
Sharpe      -4.99  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 1 / TP 0 / sell 0 / final_bar 0
Total Fees  996
```
- trades/day ≈ 1/30 ≈ 0.03

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 22)
Benchmark   -4.12%
Total Return -0.90%
CAGR        -10.75%
MDD         -0.90%
Sharpe      -5.74  (Rf=0, portfolio / full equity curve)
Sharpe      0.00  (Rf=0, trades / position holding periods only)
Trades      1  Win Rate 0% (before fees)
Profit Factor  0.00 (before fees)
SL 1 / TP 0 / sell 0 / final_bar 0
Total Fees  996
```
- trades/day ≈ 1/30 ≈ 0.03

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; nets +0.00/-0.90/-0.90%; W1는 0거래로 net>0 아님) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 0.00/0.03/0.03≪5) |
| C worst net ≥ −2% | PASS (worst Total Return -0.90%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v27` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: lower touch+RSI>signal+RSI<45 제거 → lower wick(low≤lower, close>lower) + RSI 1바 상승, 청산 BB mid/RSI60
- next_action: lower wick + RSI↑1 → mid/RSI60 — v27 백테스트.
