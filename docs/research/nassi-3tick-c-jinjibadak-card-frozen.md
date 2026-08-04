# 나씨 3틱 C (찐바닥 추매) — FROZEN

> Parent: [`nassi-3tick-b-regime-card-frozen.md`](nassi-3tick-b-regime-card-frozen.md) · 찐바닥

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | B 진입 + 음봉 짧아지며 지지할 때만 추매 |
| Code | `NassiThreeTickLongDcaC1` |
| Hypers (≤3) | `body_k=1.5` · `add_step_pct=0.002` · `max_adds=5` |

`add_step_pct` = 최소 역행 바닥(너무 얕은 추매 금지). 찐바닥 판정은 상수 규칙.

---

## Delta vs B

Entry = B (state machine + regime).

**C DCA (찐바닥 프록시):** add only if all hold:

1. `adverse ≥ add_step_pct × n_entries` (최소 거리).
2. Last 3 closed bars: red bodies **monotone shortening** `body[i] < body[i-1] < body[i-2]` (또는 마지막 2단계 단축).
3. `close ≤ rolling_min(low, 6)` 근처: `close ≤ min(low[-6:]) * 1.001` (지지/바닥권).

Exit/stake/floor same as A/B.

---

## Falsify

≥2/3 ~30d: PF < 1 or net < 0 (0-loss PF → use net).
