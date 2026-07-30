# Daytrade BB·RSI·Div 오토메이션 중간 보고서

| Field | Value |
|-------|-------|
| Branch | `automation/daytrade-bb-rsi-div` |
| As of | 2026-07-30 01:01 UTC (state.json) |
| Cadence | 10분 (이후 설정) / 초기 15분 |
| Deployed | **없음** |

Canvas: Cursor `canvases/daytrade-automation-status.canvas.tsx`

---

## Executive summary

약 **7시간+** 동안 BB+RSI(+divergence) 데이트레이드 카드 **v1 → v45**를 연속 기각했고, **v46**이 다음 백테스트로 스테이징된 상태다.  
승격 바(수익·일 5회·worst≥−2%)를 통과한 카드는 **0건**. 봇 `STRATEGY_PATH` 변경/배포 **0회**.

핸드오프(`state.json` + 리포트 push)는 동작 중이며 `consecutive_fails=45`.

---

## Headline metrics

| Metric | Value |
|--------|-------|
| Strategy JSONs | v1 … v46 (46 files) |
| Run reports | 45 (`reports/automation/daytrade-bb-rsi-div-20*.md`) |
| consecutive_fails | 45 |
| Best A-window pass | **v35** — A **2/3** (B fail: trades/day) |
| A=1/3 examples | v42, v44 |
| Deploy | `deploy_status=none`, `deployed_slug=null` |

---

## Latest completed backtest — v45

가설: RSI leave-OS30 (prior&lt;30∧≥30) while close≤BB mid; exit BB upper or RSI≥60.

| Window | Return | PF | trades/day | Benchmark |
|--------|--------|-----|------------|-----------|
| W1 06-29~07-28 | **−7.27%** | 0.88 | 2.0 | +3.26% |
| W2 05-30~06-28 | **−6.76%** | 1.05 | 2.8 | −16.19% |
| W3 04-30~05-29 | **−6.09%** | 1.11 | 2.5 | −4.12% |

승격 바: A FAIL 0/3 · B FAIL · C FAIL (worst −7.27%) · D/E PASS → **배포 안 함**.

---

## Failure modes (반복)

1. **Fee bleed** — 거래는 나오나 수수료에 엣지 잠식 (v45 등).
2. **B starve** — 일 평균 &lt; 5회 (목표 5) — v42/v44 등 A 일부 통과해도 탈락.
3. **A 0/3** — 세 윈도우 모두 net≤0 또는 거래 0에 가까움.

---

## Next (state)

- **active_card:** `daytrade-bb-rsi-div-v46`
- **hypothesis:** RSI hysteresis leave (prior&lt;35 ∧ ≥40) while close≤BB mid → exit BB upper only
- **next_action:** v46 백테스트

---

## Other automations

| Automation | Status in this report |
|------------|------------------------|
| 10m daytrade BB/RSI/div | 위 내용 (주 대상) |
| Monthly strategy review | 별개 잡; 이 기간 데이트레이드 루프와 무관 · SSH 배포 금지 |

---

## Bottom line

오토는 **이어가기·기각 루프**까지는 정상이다.  
아직 **마운트할 “괜찮은 프로핏” 카드는 없다.**
