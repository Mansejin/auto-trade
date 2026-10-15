# 월간 전략 감사 요약 (2026-09-01 UTC)

## 대상
- ACTIVE: `kimchi-rich-preposition-skip-v1`
- 레짐 엔진 스냅샷(2026-07-27): **bear** / selected=`krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6` (ACTIVE와 불일치; 엔진 갱신 지연)
- 지난달 캘린더: 2026-08-01 ~ 2026-08-31
- IMPROVER 편집(최대 2): (1) ADX≥20→25 → `v2` (2) RSI<70→55 → `v3`

## 지난달(toolkit stdout 인용)

| slug | Total Return | Benchmark | Trades | MDD |
|------|-------------:|----------:|-------:|----:|
| kimchi-rich … v1 (ACTIVE) | +1.66% | +19.73% | 40 | -6.17% |
| kimchi-rich … v2 (ADX25) | +5.69% | +19.73% | 23 | -4.51% |
| kimchi-rich … v3 (RSI55) | -2.57% | +19.73% | 23 | -5.00% |
| m5-v6 (레짐 selected) | -0.65% | +19.73% | 2 | -0.84% |

사실: 8월 B&H(+19.73%) 대비 ACTIVE·후보·v6 모두 크게 열위. v3는 ACTIVE보다도 열위 → 감사 후보에서 제외.

## 감사 게이트 (`scripts/strategy_audit.py`)
후보: `kimchi-rich-preposition-skip-v2` vs baseline ACTIVE v1, `n_trials=2`  
산출: `reports/audit/202609-kimchi-rich-v2-audit.json`

| Gate | 결과 | detail |
|------|------|--------|
| G1 | PASS | primary trades=197 min=8 |
| G2 | PASS | holdout cand=-34.6577% base=-38.7513% underperform=-4.09pp max=8.0 |
| G3 | PASS | early_oos cand=-17.5069% base=-20.4424% underperform=-2.94pp max=6.0 |
| G4 | PASS | stress_shallow_bear cand=-5.6838% base=-8.0127% |
| G5 | PASS | no complexity tax (buy=3 ind=2) |
| G6 | PASS | primary \|MDD\| cand=26.0906% base=21.705% worse=4.39pp max=5.0 |
| G8 | PASS | n_trials=2 < threshold 200 — tight bar skipped |

**판정(명시): `LIVE_OK_WITH_HUMAN`**  
reason: All LIVE audit gates passed — human may deploy; automation must NOT auto-deploy  
critiques: _(비어 있음 — 게이트 전부 critique null)_

## 낙관이 부당한 이유 (게이트 통과여도)
1. **primary 절대 수익 열위**: cand Total Return -22.5182% vs base -18.4417% (게이트는 복잡도 세금=0일 때 primary 우위 요구 없음).
2. **G6 아슬**: MDD worse 4.39pp ≈ 한도 5.0pp.
3. **holdout**: 후보·baseline 모두 Benchmark +37.9528%에 크게 패배(각각 -34.6577% / -38.7513%).
4. **stress_deep_bear**: cand -12.7339% < base -8.3526% (하드 게이트 아님).
5. **8월**: B&H +19.73% 대비 후보 +5.69% — 단기 우세만으로 “알파” 주장 금지.
6. ConditionGroup은 김치 프리미엄 skip을 인코딩하지 않음(외부 시그널; 미배선). 파라미터 편집만으로 자본 라우팅 가설을 검증한 것이 아님.
7. 레짐 스냅샷 stale(bear@2026-07-27) vs 8월 강한 상승 — 레짐-전략 정합 재검토 필요.
8. 자동화는 SSH/STRATEGY_PATH/LIVE 배포 금지. ACTIVE 파일은 이번 PR에서 **변경하지 않음**.

## 명시적 판정
- Audit verdict: **LIVE_OK_WITH_HUMAN**
- Automation action: ACTIVE 유지. 후보 JSON·감사 리포트만 기록. 사람이 리포트 읽고 전환 여부 결정.
- v3: 8월 열위 → REJECT(연구 폐기 후보, 감사 미실행).

## 디스클레이머
- upbit-strategy-toolkit은 백테스트 전용(실거래/자동주문 미지원).
- 슬리피지·호가창·부분체결 미반영.
- 과거 성과가 미래 성과를 보장하지 않음.
