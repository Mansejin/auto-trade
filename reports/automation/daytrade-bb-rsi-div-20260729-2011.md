# daytrade-bb-rsi-div 런 리포트 — 2026-07-29 20:11 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v16`
- 가설: BTC daytrade long-only: BB mid rising (mid>mid[5]) + low tags BB lower with close reclaiming above lower + RSI<40; exit BB mid or RSI≥60.
- hypers: pattern=mid_slope_lower_bounce, rsi_os=40, exit=bb_mid_or_rsi60
- fee: 툴킷 기본(Total Fees 출력 있음)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 25)
Benchmark   +3.26%
Total Return +0.58%
CAGR        +7.54%
MDD         -1.36%
Sharpe      1.50  (Rf=0, portfolio / full equity curve)
Sharpe      36.84  (Rf=0, trades / position holding periods only)
Trades      12  Win Rate 67% (before fees)
Profit Factor  2.86 (before fees)
SL 1 / TP 0 / sell 11 / final_bar 0
Total Fees  12,087
```
- trades/day ≈ 12/30 ≈ 0.40

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -16.19%
Total Return -1.23%
CAGR        -14.48%
MDD         -1.84%
Sharpe      -3.42  (Rf=0, portfolio / full equity curve)
Sharpe      -17.20  (Rf=0, trades / position holding periods only)
Trades      7  Win Rate 71% (before fees)
Profit Factor  0.67 (before fees)
SL 2 / TP 0 / sell 5 / final_bar 0
Total Fees  7,011
```
- trades/day ≈ 7/30 ≈ 0.23

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 25)
Benchmark   -4.12%
Total Return -0.50%
CAGR        -6.11%
MDD         -0.73%
Sharpe      -2.27  (Rf=0, portfolio / full equity curve)
Sharpe      16.96  (Rf=0, trades / position holding periods only)
Trades      7  Win Rate 57% (before fees)
Profit Factor  1.73 (before fees)
SL 0 / TP 0 / sell 6 / final_bar 1
Total Fees  6,978
```
- trades/day ≈ 7/30 ≈ 0.23

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (1/3; W1만 +0.58% PF2.86; W2/W3 net≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 후보 W1 trades/day 0.40≪5) |
| C worst net ≥ −2% | PASS (worst Total Return -1.23%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v17` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: mid-slope lower bounce 제거 → prior low≤BB lower 후 close가 BB mid를 한 봉에 돌파(snap-through) + RSI>rsi_signal, 청산 BB upper/RSI70
- next_action: prior low≤BB lower → close>BB mid + RSI>signal → upper/RSI70 — v17 백테스트.
