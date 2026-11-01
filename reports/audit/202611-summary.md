# 월간 전략 유지보수 요약 (2026-11-01)

## 컨텍스트
- **ACTIVE_STRATEGY**: `kimchi-rich-preposition-skip-v1`
- **regime-engine.current** (스냅샷 2026-07-27, 갱신 지연): regime=`bear`, selected=`krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6`
- **IMPROVER**: v1 → v2 파라미터 편집 **2개만** (RSI 상한 `70→55`, ADX 하한 `20→23`). 지표 추가 없음.
- **AUDIT**: `scripts/strategy_audit.py` → **LIVE_OK_WITH_HUMAN** (자동 LIVE 배포 금지)

## 지난달 (2026-10-01 ~ 2026-10-31) toolkit stdout 인용

| 전략 | Total Return | Benchmark | MDD | Trades | Win Rate | PF |
|------|--------------|-----------|-----|--------|----------|-----|
| ACTIVE v1 | **-6.44%** | -8.18% | -7.87% | 24 | 33% | 0.57 |
| candidate v2 | **-2.97%** | -8.18% | -3.61% | 13 | 23% | 0.59 |
| Policy C bear m5-v6 (참고) | **-1.68%** | -8.18% | -2.38% | 4 | 0% | 0.00 |

## 감사 게이트 (v2 vs v1)

| Gate | 결과 | detail |
|------|------|--------|
| G1 | PASS | primary trades=113 min=8 |
| G2 | PASS | holdout cand=-24.7253% base=-38.7513% underperform=-14.03pp |
| G3 | PASS | early_oos cand=-10.2698% base=-20.4424% underperform=-10.17pp |
| G4 | PASS | stress_shallow_bear cand=2.9408% base=-8.0127% |
| G5 | PASS | no complexity tax (buy=3 ind=2) |
| G6 | PASS | primary \|MDD\| cand=8.8861% base=21.705% |
| G8 | PASS | n_trials=1 < 200 |

**critiques (verbatim from audit JSON):** `[]` (게이트 전부 통과로 비어 있음)

## 무엇이 통과 / 실패했나
- **통과**: v2는 약한 베이스라인 v1 대비 전 감사 윈도우에서 상대 우위. primary Total Return `+8.21%` vs v1 `-18.44%`.
- **낙관이 부당한 이유**:
  1. 베이스라인 v1 자체가 holdout `-38.75%`, early_oos `-20.44%`로 약함 → 상대 게이트 통과 ≠ 절대 알파.
  2. v2도 holdout `-24.7253%`, early_oos `-10.2698%`로 **절대 손실**.
  3. 지난달(2026-10) v2도 `-2.97%` (벤치 `-8.18%`보다 덜 나쁨일 뿐).
  4. Policy C bear `m5-v6` primary `+17.88%` / MDD `-2.03%`가 더 강한 수치를 보임 — 이번 달 후보 범위(ACTIVE 2-edit) 밖.
  5. 김프 skip·브릿지 로직은 ConditionGroup 밖(노트) — JSON만으로 “kimchi-rich” 가설을 검증하지 않음.

## 명시적 판정
**LIVE_OK_WITH_HUMAN** — 사람이 리포트·critique·절대 손실을 읽고 ACTIVE를 `kimchi-rich-preposition-skip-v2`로 바꿀지 결정. Automation은 SSH/STRATEGY_PATH 변경·자동 LIVE 배포 하지 않음.

PR 제안: `ACTIVE_STRATEGY` → `kimchi-rich-preposition-skip-v2` (사람 승인 전제).

## 파일
- candidate: `strategies/kimchi-rich-preposition-skip-v2.json`
- audit: `reports/audit/202611-kimchi-v2-vs-v1-audit.json`
- policy: `reports/review-state/audit-policy.json`

## 고지
> 슬리피지, 호가창 유동성, 부분 체결은 반영되지 않으며 다음 캔들 시가에 전량 체결로 가정합니다.
>
> 백테스트 결과는 과거 데이터를 기초로 한 것이며, 장래 또는 실제 거래에서 동일하거나 유사한 투자 성과로 이어질 것임을 보장하지 않습니다.
