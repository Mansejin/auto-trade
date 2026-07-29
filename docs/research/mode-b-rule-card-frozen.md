# Mode B Rule Card — FROZEN

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| Stack | QQQ/USDT:USDT · US RTH · 4h structure · 15m entry |
| Style | Simple idea · mechanical execution |
| Code | `DiagonalQqqModeBFrozenV1` |
| Hypers (≤3) | `vol_k=1.5` · `retest_bars=96` · `max_slope_pct=0.015` |

Do **not** retune hypers after a fail. Falsify → revise hypothesis / card, not knobs.

---

## Rules

1. **Structure** — 4h volume-pivot parallel channel; valid rails;  
   `abs(ch_slope)/mid ≤ max_slope_pct` (steep skip).
2. **Break (heads-up)** — 15m **close** outside rail **and**  
   `volume ≥ vol_k × SMA20(volume)`. No chase on break bar.
3. **Entry** — within `retest_bars` after break, price revisits rail **with rejection**:  
   - Long: retest upper, `close > open`, close holds ≥ rail zone  
   - Short: retest lower, `close < open`, close holds ≤ rail zone  
   Rejection missing → skip (S19).
4. **Session** — US RTH 09:30–16:00 America/New_York only.
5. **Exit** — ROI / stoploss only (no mid-rail auto-exit).  
   Backup ROI ≈ 1.0%, SL ≈ −0.8% (proxy for 0.5×width / fail; not a 4th hyper).

---

## Falsify

≥2/3 independent ~30d windows: PF < 1.0 **or** net < 0 → **falsified**.  
Sparse OK (~1 trade / 2 days). Promote to LIVE/SCALP: **no** until survive.

---

## Sources

[`edwards-murphy-excerpts.md`](edwards-murphy-excerpts.md) · [`channel-clearest3-ict-overlay.md`](channel-clearest3-ict-overlay.md) · Batch1 S15–16 gold / S19 rejection lesson.
