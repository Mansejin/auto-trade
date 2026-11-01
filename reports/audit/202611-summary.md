# 월간 전략 감사 요약 (2026-11-01, 리뷰 대상: 2026-10)

## 식별
- ACTIVE_STRATEGY: `kimchi-rich-preposition-skip-v1` (변경 없음)
- regime-engine.json `current` 스냅샷: bear @ 2026-07-27 (stale; selected 기록은 예전 m5-v6)
- `scripts/regime_select.py` 재계산 (2026-10-31 마감봉): **transition** → `strategies/regime-bull-trend-4h-v2.json` (백테스트 선택기만, LIVE 주문 없음)
- 편집 한도: 파라미터 2개 (v4=RSI buy 70→65, v5=ADX 20→23)

## 2026-10 달력월 toolkit stdout (인용)

| slug | total_return_pct | benchmark_pct | mdd_pct | trades |
|------|------------------|---------------|---------|--------|
| v1 (ACTIVE) | -6.4418 | -8.1482 | -7.8666 | 24 |
| v4 (RSI&lt;65) | -6.1343 | -8.1482 | -7.7578 | 22 |
| v5 (ADX≥23) | -3.3562 | -8.1482 | -5.2326 | 22 |

10월 B&H는 -8.1482%. ACTIVE·후보 모두 음수이나 benchmark 대비 소폭 덜 손실. 월간만으로 승격 근거 삼지 않음.

## 감사 게이트 (`scripts/strategy_audit.py`, n_trials=2)

### v4 vs v1 → **LIVE_OK_WITH_HUMAN**
- primary: cand=-15.6071 n=267 | base=-18.4417 n=282
- early_oos: cand=-22.4633 | base=-20.4424
- holdout: cand=-40.9251 | base=-38.7513
- shallow_bear: cand=-5.0112 | base=-8.0127
- critiques (verbatim): `[]`

### v5 vs v1 → **REJECT**
- primary: cand=-13.5002 n=228 | base=-18.4417 n=282
- early_oos: cand=-15.5806 | base=-20.4424
- holdout: cand=-33.0133 | base=-38.7513
- shallow_bear: cand=-9.7701 | base=-8.0127 (**G4 FAIL**)
- critiques (verbatim):
  - `Regressed on known shallow-bear failure mode`

## 낙관이 부적절 한 이유 (감사팀)
- v5는 하드 게이트 G4 실패 → LIVE 후보 금지. 10월 월간이 나아 보여도 shallow-bear 회귀가 우선.
- v4는 게이트 통과이나 critiques 비어 있음 ≠ 자동 배포. Automation은 LIVE/SSH/STRATEGY_PATH 변경 안 함.
- holdout에서 v4도 -40.9251% (B&H +37.9528) — 장기 우위 주장 불가.
- ConditionGroup JSON만 감사; 김치 프리미엄 skip은 bot 레이어 미배선.
- 슬리피지/호가/부분체결 미반영.

## 명시적 판정
- **공식 판정**: v4=`LIVE_OK_WITH_HUMAN`, v5=`REJECT`
- **감사팀 운영 태도**: ACTIVE_STRATEGY **유지(v1)**. v5 폐기(연구 기록만). v4는 후보 JSON만 보관. LIVE 반영은 사람만.
- SSH / STRATEGY_PATH / bot 배포: **하지 않음**
- daytrade 10분 자동화 브랜치: **미접촉**

## 산출물
- `strategies/kimchi-rich-preposition-skip-v4.json`
- `strategies/kimchi-rich-preposition-skip-v5.json`
- `reports/audit/202611-kimchi-v4-vs-v1-audit.json`
- `reports/audit/202611-kimchi-v5-vs-v1-audit.json`

## Disclaimer
- 과거 백테스트가 미래 성과를 보장하지 않음.
- 슬리피지·유동성·부분체결은 모델되지 않음.
- upbit-strategy-toolkit은 backtest-only (LIVE 거래 지원 주장 금지).
