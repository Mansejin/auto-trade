# BTC Swing-Box Fade — FROZEN

> Parent line: day-box V1/V2 기각 · **고정 스윙 S/R** (롤링 Donchian 폐기)

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | 확정 스윙고·저로 1–2% 박스를 고정하고, 각 변 **≥2터치** 후 리젝션만 페이드 |
| Universe | BTC USDT-perp, 24h |
| TF | 15m |
| Lev | 5 |
| Code | `BtcSwingBoxFadeV1` |
| Hypers (≤3) | `touch_frac=0.15` · `wick_body_k=1.5` · `min_touches=2` |

Do **not** retune after fail.

---

## Rules

1. **Pivot** (no lookahead): `pivot_left=3`. At bar `i`, if `high[i-3]` is max of `high[i-6..i]`, confirm swing high = `high[i-3]` (mirror for low).
2. **Box**: last confirmed swing high + last confirmed swing low. Valid only if `0.01 ≤ (hh−ll)/mid ≤ 0.02`. New pivot that keeps width in band **replaces** the box and resets touch counts.
3. **Touches**: bar counts as high-touch if `high ≥ hh − touch_frac×span`; low-touch if `low ≤ ll + touch_frac×span`. Need `touches_h ≥ min_touches` before shorts, `touches_l ≥ min_touches` before longs.
4. **Entry**: rejection wick + reclaim through edge band (same as box V2), and touch quota met. Cooldown 6 bars after signal.
5. **Invalidate**: `close > hh` or `close < ll` → clear box (no entries until new valid swing pair).
6. **TP**: box mid. **SL**: rejection candle extreme. Floor −15% lev.
7. **ADX**: constant pause if `ADX(14) ≥ 25` (not a hyper).

---

## Falsify

≥2/3 ~30d: **PF < 1 or net < 0** → falsified.
