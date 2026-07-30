# daytrade-bb-rsi-div 런 리포트 — 2026-07-30 00:31 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v42`
- 가설: BTC daytrade long-only: RSI leave-oversold (prior<30, current≥30) while close≤BB lower; exit BB mid or RSI≥50.
- hypers: pattern=rsi_leave_os30_at_lower, exit=bb_mid_or_rsi50, rsi_os=30
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -1.53%
CAGR        -17.61%
MDD         -1.64%
Sharpe      -6.24  (Rf=0, portfolio / full equity curve)
Sharpe      -39.68  (Rf=0, trades / position holding periods only)
Trades      5  Win Rate 60% (before fees)
Profit Factor  0.35 (before fees)
SL 2 / TP 0 / sell 3 / final_bar 0
Total Fees  4,946
```
- trades/day ≈ 5/30 ≈ 0.17

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -1.10%
CAGR        -12.96%
MDD         -1.65%
Sharpe      -2.76  (Rf=0, portfolio / full equity curve)
Sharpe      -12.50  (Rf=0, trades / position holding periods only)
Trades      5  Win Rate 40% (before fees)
Profit Factor  0.68 (before fees)
SL 2 / TP 0 / sell 3 / final_bar 0
Total Fees  4,981
```
- trades/day ≈ 5/30 ≈ 0.17

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return +0.02%
CAGR        +0.23%
MDD         -0.86%
Sharpe      0.10  (Rf=0, portfolio / full equity curve)
Sharpe      41.44  (Rf=0, trades / position holding periods only)
Trades      5  Win Rate 80% (before fees)
Profit Factor  3.03 (before fees)
SL 0 / TP 0 / sell 5 / final_bar 0
Total Fees  4,999
```
- trades/day ≈ 5/30 ≈ 0.17

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (1/3; W3만 +0.02%/PF3.03, W1/W2 net−) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 W3≈0.17 ≪5) |
| C worst net ≥ −2% | PASS (worst Total Return -1.53%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v43` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: RSI leave-OS30@lower→mid/RSI50 제거 → wick reject(low≤lower∧close>lower) + RSI<35; 청산 BB mid or RSI≥50
- next_action: wick reject (low≤lower∧close>lower) RSI<35 → mid/RSI50 — v43 백테스트.
