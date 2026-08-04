# 나씨 3틱 상태머신 (A) — FROZEN

> Parent: [`nassi-3tick-long-dca-card-frozen.md`](nassi-3tick-long-dca-card-frozen.md) · 정리본 틱 카운트

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | 상태머신으로 음봉 틱 3회 집계 후 롱 + 1/40 DCA |
| Universe | BTC USDT-perp, 24h |
| TF | 5m |
| Side | Long only |
| Code | `NassiThreeTickLongDcaA1` |
| Hypers (≤3) | `body_k=1.5` · `add_step_pct=0.004` · `max_adds=5` |

Do **not** retune. Next cards: B=장 필터, C=찐바닥 추매.

---

## Delta vs parent (V1 consecutive)

V1 = 단순 3연속 meaningful red.  
**A** = 정리본 상태머신:

1. Meaningful red만 틱 (`body ≥ body_k × med`).
2. 직전 틱 대비 `body < 0.5 × prev_tick` → **세지 않음** (카운트 유지).
3. Non-meaningful 봉 `sideways_reset=3` 연속 → **카운트 리셋**.
4. Meaningful green → **리셋**.
5. 첫 틱: 직전이 더 긴 양봉이면, 종가가 그 양봉 시가 아래일 때만 1틱.
6. 3틱 도달 시 진입 신호 후 카운트 리셋.

Keep from parent: pump skip, min_run 0.3%, 1/40 stake, DCA step, avg_reclaim, −20% floor.

---

## Falsify

≥2/3 ~30d: **PF < 1 or net < 0** (0-loss PF=0.00 → use net).
