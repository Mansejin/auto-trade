# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 19:11 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v10`
- 가설: BTC daytrade long-only: OR of (BB lower + regular bull LL/HL lookback4 RSI<48) OR (BB mid + hidden bull HL/LL lookback4 RSI<48); exit BB mid or RSI≥55.
- hypers: lookback=4, rsi_cap=48, exit=bb_mid_or_rsi55
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 26)
Benchmark   +3.26%
Total Return +0.02%
CAGR        +0.30%
MDD         -0.69%
Sharpe      0.10  (Rf=0, portfolio / full equity curve)
Sharpe      58.59  (Rf=0, trades / position holding periods only)
Trades      9  Win Rate 67% (before fees)
Profit Factor  4.04 (before fees)
SL 0 / TP 0 / sell 9 / final_bar 0
Total Fees  8,979
```
- trades/day ≈ 9/30 ≈ 0.30

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -16.19%
Total Return -0.93%
CAGR        -11.05%
MDD         -2.64%
Sharpe      -1.94  (Rf=0, portfolio / full equity curve)
Sharpe      1.80  (Rf=0, trades / position holding periods only)
Trades      10  Win Rate 70% (before fees)
Profit Factor  1.03 (before fees)
SL 3 / TP 0 / sell 7 / final_bar 0
Total Fees  9,928
```
- trades/day ≈ 10/30 ≈ 0.33

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 26)
Benchmark   -4.12%
Total Return -2.22%
CAGR        -24.57%
MDD         -2.54%
Sharpe      -7.65  (Rf=0, portfolio / full equity curve)
Sharpe      -44.47  (Rf=0, trades / position holding periods only)
Trades      7  Win Rate 57% (before fees)
Profit Factor  0.15 (before fees)
SL 2 / TP 0 / sell 5 / final_bar 0
Total Fees  6,919
```
- trades/day ≈ 7/30 ≈ 0.23

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (1/3; W1만 +0.02% PF4.04) |
| B 통과 윈도우 trades/day≥5 | FAIL (W1 0.30≪5; 통과 윈도우 부족) |
| C worst net ≥ −2% | FAIL (worst Total Return -2.22%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v11` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: 스윙 다이버전스 OR 제거 → prior BB lower 터치 후 현재 리클레임 + RSI↑1·RSI<50, 청산 BB mid/RSI55
- next_action: BB lower tag-then-reclaim + RSI↑1 RSI<50 → mid/RSI55 — v11 백테스트.
