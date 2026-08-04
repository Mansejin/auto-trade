# 나씨 3틱 B (장 필터) — FROZEN

> Parent: [`nassi-3tick-a-statemachine-card-frozen.md`](nassi-3tick-a-statemachine-card-frozen.md) · 낄끼빠빠

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | A 진입 + 상승추세·저변동 횡보 스킵 |
| Code | `NassiThreeTickLongDcaB1` |
| Hypers (≤3) | `body_k=1.5` · `add_step_pct=0.004` · `max_adds=5` |

---

## Delta vs A

Keep A tick state machine + DCA.

**B filters (constants):**

1. **No uptrend**: `close < SMA(50)` (상승 중 찔끔 하락 금지 프록시).
2. **No dead chop**: `ATR(14)/close ≥ 0.0015` (저변동 횡보 단타 금지 프록시).

---

## Falsify

≥2/3 ~30d: PF < 1 or net < 0 (0-loss PF → use net).
