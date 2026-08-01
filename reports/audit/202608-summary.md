# 2026-08 월간 전략 감사 요약

- 기준일: 2026-08-01 (cron UTC 09:00; 지난달 = 2026-07)
- ACTIVE_STRATEGY: `krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6`
- regime-engine current (as of 2026-07-27): **bear**
- IMPROVER 편집 수: 1건 반영 후보(v8 RSI55→58). SL2.5 시도(v8b)는 해당 창에서 SL 미발동으로 무효 → 폐기.
- LIVE/SSH/`STRATEGY_PATH` 원격 변경: 없음

## 지난달(2026-07-01 ~ 2026-07-26) toolkit stdout (인용)

### ACTIVE v6
- Benchmark   +5.83%
- Total Return +2.68%
- MDD         -1.09%
- Trades      6

### baseline v3 (참고)
- Total Return +3.93%
- Trades      8

### candidate v8 (RSI buy 55→58)
- Total Return +2.07%
- MDD         -1.68%
- Trades      7

## Audit Team (`scripts/strategy_audit.py`)

- candidate: `strategies/krw-btc-1h-ema-adx23-rsi58-sl3-tp45-m5-v8.json`
- baseline: `strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json`
- n_trials: 10
- report: `reports/audit/202608-krw-btc-1h-ema-adx23-rsi58-sl3-tp45-m5-v8-audit.json`

### Gates
- PASS G1 min_trades_primary: primary trades=34 min=8
- PASS G2 holdout_not_collapse: holdout cand=-1.13% base=-1.5% underperform=-0.37pp
- PASS G3 early_oos: early_oos cand=-4.88% base=-3.31% underperform=1.57pp
- FAIL G4 no_shallow_bear_regression: stress_shallow_bear cand=-7.68% base=-1.22%
- PASS G5 complexity_tax
- PASS G6 mdd_guard
- PASS G8 (n_trials < 200)

### 명시적 판정: **REJECT**

Hard reject: G4. shallow-bear 스트레스 창에서 ACTIVE 대비 회귀(-7.68% vs -1.22%).

## 왜 낙관이 부적합한가

- 지난달 ACTIVE도 B&H(+5.83%)를 하회했고, 후보 v8은 지난달·primary 모두 ACTIVE보다 약했다.
- 거래 수만 늘린 RSI 완화는 holdout에서 소폭 나았으나, 알려진 약점(shallow bear)에서 크게 무너졌다 — in-sample 거래 밀도 개선 ≠ 일반화.
- Audit Team 정책상 G4 실패는 LIVE/ACTIVE 교체 제안 금지.

## 조치

- ACTIVE_STRATEGY 유지 (`…-m5-v6`)
- v8는 research archive로만 보관; promote-to-LIVE PR 없음
- research notes PR만 오픈

## Disclaimer

- upbit-strategy-toolkit은 백테스트 전용이며 라이브 트레이딩을 지원하지 않는다.
- 과거 성과가 미래 성과를 보장하지 않는다.
- 슬리피지·호가·부분체결은 모델되지 않는다.
