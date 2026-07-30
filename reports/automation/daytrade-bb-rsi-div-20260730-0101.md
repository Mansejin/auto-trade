# daytrade-bb-rsi-div 런 리포트 — 2026-07-30 01:01 UTC

## 카드
- slug: `daytrade-bb-rsi-div-v45`
- 가설: BTC daytrade long-only: RSI leave-OS30 (prior<30∧≥30) while close≤BB middle; exit BB upper or RSI≥60.
- hypers: pattern=leave_os30_below_mid, exit=bb_upper_or_rsi60, rsi_os=30
- fee: 툴킷 기본(Total Fees 출력)

## 윈도우 결과 (stdout 인용)

### W1 2026-06-29 ~ 2026-07-28
```
Period      2026-06-29 ~ 2026-07-28 (UTC) (trading bars: 8296, warmup bars: 23)
Benchmark   +3.26%
Total Return -7.27%
CAGR        -61.32%
MDD         -8.32%
Sharpe      -6.49  (Rf=0, portfolio / full equity curve)
Sharpe      -3.24  (Rf=0, trades / position holding periods only)
Trades      60  Win Rate 65% (before fees)
Profit Factor  0.88 (before fees)
SL 14 / TP 0 / sell 45 / final_bar 1
Total Fees  57,862
```
- trades/day ≈ 60/30 ≈ 2.0

### W2 2026-05-30 ~ 2026-06-28
```
Period      2026-05-30 ~ 2026-06-28 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -16.19%
Total Return -6.76%
CAGR        -58.55%
MDD         -9.70%
Sharpe      -3.64  (Rf=0, portfolio / full equity curve)
Sharpe      1.84  (Rf=0, trades / position holding periods only)
Trades      84  Win Rate 55% (before fees)
Profit Factor  1.05 (before fees)
SL 35 / TP 2 / sell 47 / final_bar 0
Total Fees  80,522
```
- trades/day ≈ 84/30 ≈ 2.8

### W3 2026-04-30 ~ 2026-05-29
```
Period      2026-04-30 ~ 2026-05-29 (UTC) (trading bars: 8353, warmup bars: 23)
Benchmark   -4.12%
Total Return -6.09%
CAGR        -54.63%
MDD         -9.30%
Sharpe      -5.29  (Rf=0, portfolio / full equity curve)
Sharpe      2.39  (Rf=0, trades / position holding periods only)
Trades      75  Win Rate 68% (before fees)
Profit Factor  1.11 (before fees)
SL 14 / TP 0 / sell 61 / final_bar 0
Total Fees  74,401
```
- trades/day ≈ 75/30 ≈ 2.5

## 승격 바
| 항목 | 결과 |
|------|------|
| A ≥2/3 net>0 & (PF≥1.2 or zero-loss) | FAIL (0/3; 전부 net≤0) |
| B 통과 윈도우 trades/day≥5 | FAIL (통과 윈도우 없음; 최대 ≈2.8) |
| C worst net ≥ −2% | FAIL (worst Total Return -7.27%) |
| D fee on | PASS (Total Fees 출력) |
| E same encoding | PASS |

**verdict: FAIL — 배포 안 함**

## 다음 카드 (구조 개정, 하이퍼 재튜닝 금지)
- slug: `daytrade-bb-rsi-div-v46` (JSON 저장·validate OK, 백테스트는 다음 런)
- 구조 변경: leave-OS30@mid→upper/RSI60 제거 → RSI hysteresis leave(prior<35∧≥40) while close≤BB mid; 청산 BB upper only (단일 임계 leave-OS 폐기, RSI 조기청산 제거)
- next_action: RSI hysteresis 35→40 + close≤BB mid → upper only — v46 백테스트.
