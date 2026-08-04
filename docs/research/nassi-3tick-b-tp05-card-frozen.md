# 나씨 3틱 B + loose reclaim TP — FROZEN

> Parent: [`nassi-3tick-b-regime-card-frozen.md`](nassi-3tick-b-regime-card-frozen.md) · TP 점검 후속

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | B 진입/DCA 그대로, 평단 회복 청산을 **+0.5%** net로 |
| Code | `NassiThreeTickLongDcaB1Tp05` |
| Hypers (≤3) | `body_k=1.5` · `add_step_pct=0.004` · `max_adds=5` (B와 동일) |

Do **not** retune. Exit threshold is a **card constant**, not a 4th hyper.

---

## Delta vs B

| | B | This |
|--|---|------|
| `avg_reclaim` | `current_profit ≥ 0.001` (0.1%) | `≥ 0.005` (0.5%) |
| SL | −20% | −20% |

Entry / regime / 1/40 / DCA unchanged.

Hypothesis: tighter 0.1% reclaim clips winners; 0.5% improves net without bringing back June-style ruin.

---

## Falsify

≥2/3 ~30d: **PF < 1 or net < 0** (0-loss PF → use net). Also compare to B nets on same windows (factual, not retune).
