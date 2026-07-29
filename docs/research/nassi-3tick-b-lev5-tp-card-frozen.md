# 나씨 3틱 B + lev5 + TP 3~5% — FROZEN

> Parent: [`nassi-3tick-b-regime-card-frozen.md`](nassi-3tick-b-regime-card-frozen.md)

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | B 진입/DCA, **lev 5**, 평단 청산 **+3% / +5%** (수수료 포함 profit ratio) |
| Codes | `NassiThreeTickLongDcaB1Lev5Tp03` · `NassiThreeTickLongDcaB1Lev5Tp05` |
| Hypers (≤3) | `body_k=1.5` · `add_step_pct=0.004` · `max_adds=5` |

---

## Delta vs B

| | B | This |
|--|---|------|
| Leverage | 1 (default) | **5** |
| `avg_reclaim` | +0.1% | **+3%** or **+5%** net profit ratio |
| `stoploss` | −20% | −20% (same ratio) |

freqtrade `current_profit` = price move × leverage (fees in). So:

- TP +3% @ 5x ≈ **+0.6% price**
- TP +5% @ 5x ≈ **+1.0% price**
- SL −20% @ 5x ≈ **−4% price** (tighter in price than 1x −20%)

Entry / regime / 1/40 / DCA unchanged.

---

## Falsify

Each code separately: ≥2/3 ~30d **PF < 1 or net < 0** (0-loss PF → use net).
