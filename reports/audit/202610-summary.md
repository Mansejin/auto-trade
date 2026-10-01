# 월간 전략 감사 요약 (2026-10-01, 리뷰 대상: 2026-09)

## 식별
- ACTIVE_STRATEGY: `kimchi-rich-preposition-skip-v1` (변경 없음)
- regime-engine.json `current`: bear @ 2026-07-27 (스냅샷 stale; selected 기록은 예전 m5-v6)
- 편집 한도: 파라미터 2개 (v2=ADX 20→25, v3=RSI buy 70→60)

## 2026-09 달력월 toolkit stdout (인용)

| slug | total_return_pct | benchmark_pct | mdd_pct | trades |
|------|------------------|---------------|---------|--------|
| v1 (ACTIVE) | -3.8468 | +4.5572 | -9.5406 | 35 |
| v2 (ADX≥25) | -8.0156 | +4.5572 | -8.4429 | 18 |
| v3 (RSI&lt;60) | -3.1749 | +4.5572 | -6.6777 | 27 |

9월은 B&H(+4.5572%) 대비 세 전략 모두 음수. v2는 거래 수를 줄였으나 손실이 더 큼. v3만 소폭 손실 완화.

## 감사 게이트 (`scripts/strategy_audit.py`)

### v2 vs v1 → **LIVE_OK_WITH_HUMAN**
- primary: cand=-22.5182 n=197 | base=-18.4417 n=282
- early_oos: cand=-17.5069 | base=-20.4424
- holdout: cand=-34.6577 | base=-38.7513
- shallow_bear: cand=-5.6838 | base=-8.0127
- critiques (verbatim): `[]`

### v3 vs v1 → **LIVE_OK_WITH_HUMAN**
- primary: cand=-5.9088 n=229 | base=-18.4417 n=282
- early_oos: cand=-17.4148 | base=-20.4424
- holdout: cand=-32.7027 | base=-38.7513
- shallow_bear: cand=-1.1267 | base=-8.0127
- critiques (verbatim): `[]`

## 낙관이 부적절 한 이유 (감사팀)
- 게이트 통과 ≠ LIVE 권고. Automation은 자동 배포하지 않음.
- 9월 실측: ACTIVE·후보 모두 benchmark 대비 열위 (`total_return_pct` 음수, B&H +4.5572).
- holdout에서 v3도 -32.7027% (B&H +37.9528) — 장기 알파 주장 불가.
- ConditionGroup JSON만 감사; 김치 프리미엄 skip은 아직 bot 레이어에 미배선.
- 슬리피지/호가/부분체결 미반영.

## 명시적 판정
- **공식 판정 (감사 스크립트)**: v2·v3 모두 `LIVE_OK_WITH_HUMAN`
- **감사팀 운영 태도**: ACTIVE_STRATEGY는 **유지(v1)**. v3를 후보로만 남김. LIVE 반영은 사람만.
- SSH / STRATEGY_PATH / bot 배포: **하지 않음**
- daytrade 10분 자동화 브랜치: **미접촉**

## 산출물
- `strategies/kimchi-rich-preposition-skip-v2.json`
- `strategies/kimchi-rich-preposition-skip-v3.json`
- `reports/audit/202610-kimchi-v2-vs-v1-audit.json`
- `reports/audit/202610-kimchi-v3-vs-v1-audit.json`

## Disclaimer
- 과거 백테스트가 미래 성과를 보장하지 않음.
- 슬리피지·유동성·부분체결은 모델되지 않음.
- upbit-strategy-toolkit은 backtest-only (LIVE 거래 지원 주장 금지).
